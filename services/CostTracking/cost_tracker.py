"""
Cost Tracker - Tracks API call costs for sessions
"""

import os
import asyncio
from datetime import datetime
from managers.mongodb_manager import mongo_db
from shared.logging_config import get_logger

logger = get_logger(__name__)


class CostTracker:
    """Track API call costs for a session"""

    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        self.started_at = datetime.utcnow()

    def start_session(self):
        """Initialize session cost tracking in MongoDB"""
        mongo_db.session_costs.insert_one({
            "session_id": self.session_id,
            "user_id": self.user_id,
            "started_at": self.started_at,
            "ended_at": None,
            "status": "active",
            "api_calls": {
                "tutor_api": {
                    "count": 0,
                    "estimated_cost": 0.0,
                    "prompt_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0
                },
                "teaching_assistant": {"count": 0, "estimated_cost": 0.0},
                "dash_api": {"count": 0, "estimated_cost": 0.0}
            },
            "tutor_token_usage": [],
            "total_estimated_cost": 0.0,
            "snapshots": []
        })
        logger.info(f"[COST_TRACKER] Started tracking costs for session {self.session_id}")

    def increment_api_call(self, api_type: str):
        """Increment API call counter for this session"""
        mongo_db.session_costs.update_one(
            {"session_id": self.session_id},
            {"$inc": {f"api_calls.{api_type}.count": 1}}
        )

    async def update_costs(self):
        """Periodic update of cost estimates - runs every interval"""
        elapsed = (datetime.utcnow() - self.started_at).total_seconds()

        # Determine next interval based on elapsed time
        interval = self._get_interval(elapsed)

        # Fetch current API counts
        session = mongo_db.session_costs.find_one({"session_id": self.session_id})

        if not session:
            return

        # Calculate costs
        total_cost = self._calculate_total_cost(session["api_calls"])

        # Update MongoDB
        mongo_db.session_costs.update_one(
            {"session_id": self.session_id},
            {
                "$set": {"total_estimated_cost": total_cost},
                "$push": {
                    "snapshots": {
                        "timestamp": datetime.utcnow(),
                        "interval": f"{interval}s",
                        "api_counts": session["api_calls"],
                        "total_cost": total_cost
                    }
                }
            }
        )

        logger.debug(f"[COST_TRACKER] Updated costs for session {self.session_id}")

        # Schedule next update
        await asyncio.sleep(interval)
        await self.update_costs()

    def _get_interval(self, elapsed: float) -> int:
        """Determine update interval based on session duration"""
        from services.shared.pricing_config import COST_TRACKING_INTERVALS

        for threshold, interval in sorted(COST_TRACKING_INTERVALS.items()):
            if elapsed < threshold:
                return interval
        return 300  # Default to 5 minutes

    def _calculate_total_cost(self, api_calls: dict) -> float:
        """Calculate total cost from API calls and token usage"""
        from services.shared.pricing_config import API_PRICING, GEMINI_TOKEN_PRICING

        total = 0.0
        
        # TeachingAssistant (OpenRouter) - per call (if used)
        total += api_calls.get("teaching_assistant", {}).get("count", 0) * API_PRICING["openrouter"]
        
        # Tutor API (Gemini Live) - token-based
        tutor_data = api_calls.get("tutor_api", {})
        prompt_tokens = tutor_data.get("prompt_tokens", 0)
        output_tokens = tutor_data.get("output_tokens", 0)
        
        # Calculate cost based on tokens
        # Gemini Live API uses audio input
        if prompt_tokens > 0:
            input_cost = (prompt_tokens / 1_000_000) * GEMINI_TOKEN_PRICING["audio_input"]
            total += input_cost
        
        if output_tokens > 0:
            output_cost = (output_tokens / 1_000_000) * GEMINI_TOKEN_PRICING["output"]
            total += output_cost
        
        # DASH API - Free
        total += api_calls.get("dash_api", {}).get("count", 0) * API_PRICING["dash_api"]
        
        return round(total, 4)

    def end_session(self):
        """Finalize session cost tracking"""
        # Fetch current session data
        session = mongo_db.session_costs.find_one({"session_id": self.session_id})
        
        if not session:
            logger.warning(f"[COST_TRACKER] Session {self.session_id} not found for cost calculation")
            # Still mark as ended even if not found
            mongo_db.session_costs.update_one(
                {"session_id": self.session_id},
                {
                    "$set": {
                        "ended_at": datetime.utcnow(),
                        "status": "completed"
                    }
                }
            )
            return
        
        # Get API calls data
        api_calls = session.get("api_calls", {})
        tutor_data = api_calls.get("tutor_api", {})
        
        # Ensure all required API structures exist in api_calls dict
        if "tutor_api" not in api_calls:
            api_calls["tutor_api"] = {}
        if "teaching_assistant" not in api_calls:
            api_calls["teaching_assistant"] = {"count": 0, "estimated_cost": 0.0}
        if "dash_api" not in api_calls:
            api_calls["dash_api"] = {"count": 0, "estimated_cost": 0.0}
        
        # Calculate output tokens if they're 0 but we can derive them from total_tokens
        prompt_tokens = tutor_data.get("prompt_tokens", 0)
        output_tokens = tutor_data.get("output_tokens", 0)
        total_tokens = tutor_data.get("total_tokens", 0)
        
        # If output_tokens is 0 but total_tokens > prompt_tokens, calculate output tokens
        if output_tokens == 0 and total_tokens > prompt_tokens:
            calculated_output_tokens = total_tokens - prompt_tokens
            # Update output_tokens in the document
            mongo_db.session_costs.update_one(
                {"session_id": self.session_id},
                {"$set": {"api_calls.tutor_api.output_tokens": calculated_output_tokens}}
            )
            output_tokens = calculated_output_tokens
            # Update api_calls dict for cost calculation
            api_calls["tutor_api"]["output_tokens"] = calculated_output_tokens
        
        # Calculate total cost using the existing method
        total_cost = self._calculate_total_cost(api_calls)
        
        # Calculate individual API costs for detailed breakdown
        from services.shared.pricing_config import API_PRICING, GEMINI_TOKEN_PRICING
        
        # Tutor API cost (token-based)
        tutor_cost = 0.0
        if prompt_tokens > 0:
            input_cost = (prompt_tokens / 1_000_000) * GEMINI_TOKEN_PRICING["audio_input"]
            tutor_cost += input_cost
        
        if output_tokens > 0:
            output_cost = (output_tokens / 1_000_000) * GEMINI_TOKEN_PRICING["output"]
            tutor_cost += output_cost
        
        # TeachingAssistant cost (per call)
        ta_count = api_calls.get("teaching_assistant", {}).get("count", 0)
        ta_cost = ta_count * API_PRICING["openrouter"]
        
        # DASH API is free
        dash_cost = 0.0
        
        # Update MongoDB with final costs
        mongo_db.session_costs.update_one(
            {"session_id": self.session_id},
            {
                "$set": {
                    "ended_at": datetime.utcnow(),
                    "status": "completed",
                    "total_estimated_cost": round(total_cost, 4),
                    "api_calls.tutor_api.estimated_cost": round(tutor_cost, 4),
                    "api_calls.teaching_assistant.estimated_cost": round(ta_cost, 4),
                    "api_calls.dash_api.estimated_cost": dash_cost
                }
            }
        )
        logger.info(f"[COST_TRACKER] Ended tracking costs for session {self.session_id}, total cost: ${round(total_cost, 4)}")
