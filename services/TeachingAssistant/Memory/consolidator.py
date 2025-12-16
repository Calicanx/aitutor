import os
import sys
import json
import time
import asyncio
from typing import Dict, Any, List
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.logging_config import get_logger
from .schema import MemoryType
from .vector_store import MemoryStore
from .extractor import MemoryExtractor
from ..core.decorators import with_retry, with_circuit_breaker, CircuitBreaker
from ..core.exceptions import LLMGenerationError

logger = get_logger(__name__)

# Circuit breaker for LLM services
llm_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

class SessionClosingCache:
    # Number of user-adam exchanges to collect before triggering memory generation
    USER_EXCHANGES_FOR_MEMORY_GENERATION = 3
    
    def __init__(self, session_id: str, user_id: str):
        self.session_id = session_id
        self.user_id = user_id
        # Lock not strictly needed if running in single async event loop task, 
        # but kept for safety if multi-threaded app structure persists.
        # Switched to asyncio.Lock for async context if needed, but here we keep simple logic.
        self._lock = asyncio.Lock()
        self.cache = {
            "new_memories": [],
            "emotional_arc": [],
            "key_moments": [],
            "unfinished_topics": [],
            "topics_covered": [],
            "session_summary": "",
            "goodbye_message": "",
            "next_session_hooks": []
        }
        # Buffer to store exchanges before batch processing
        self.exchange_buffer = []

        # Clear any existing closing cache from previous session
        self.clear_closing_cache()

    
    def clear_closing_cache(self):
        """Clear closing cache file at the start of a new session."""
        try:
            data_dir = f"services/TeachingAssistant/Memory/data/{self.user_id}/memory/TeachingAssistant"
            file_path = f"{data_dir}/TA-closing-retrieval.json"
            
            # Use os.makedirs to ensure directory exists (exist_ok=True)
            os.makedirs(data_dir, exist_ok=True)
            
            # Initialize with empty structure
            closing_data = {
                "session_id": self.session_id,
                "timestamp": time.time(),
                "new_memories": [],
                "emotional_arc": [],
                "key_moments": [],
                "unfinished_topics": [],
                "topics_covered": [],
                "session_summary": "",
                "goodbye_message": "",
                "next_session_hooks": []
            }
            
            # Always overwrite/create the file with empty data
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(closing_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Cleared closing cache for new session: {self.session_id}")

        except Exception as e:
            logger.error(f"Error clearing closing cache: {e}", exc_info=True)

    async def update_after_exchange(self, student_text: str, ai_text: str, topic: str, extractor: MemoryExtractor, store: MemoryStore):
        """
        Buffer exchanges and extract memories in batches of 3.
        This is called when we receive broadcasts from server.js.
        Thread-safe to avoid race conditions between concurrent updates.
        """
        async with self._lock:
            # Buffer the exchange if we have both sides of the dialogue
            if student_text and ai_text:
                self.exchange_buffer.append({
                    "student_text": student_text,
                    "ai_text": ai_text,
                    "topic": topic or "general"
                })
                
                # Track topics (simple deduplication)
                if topic and topic not in self.cache["topics_covered"]:
                    self.cache["topics_covered"].append(topic)
                
                logger.debug(
                    "Buffered exchange %s/%s",
                    len(self.exchange_buffer),
                    self.USER_EXCHANGES_FOR_MEMORY_GENERATION,
                )

                # Process batch when we reach the threshold
                if len(self.exchange_buffer) >= self.USER_EXCHANGES_FOR_MEMORY_GENERATION:
                    await self._process_exchange_batch(extractor, store)
            else:
                logger.warning(
                    "Missing text for buffering - student_text: %s, ai_text: %s",
                    bool(student_text),
                    bool(ai_text),
                )
    
    async def _process_exchange_batch(self, extractor: MemoryExtractor, store: MemoryStore):
        """Process buffered exchanges and extract memories."""
        # Caller must hold self._lock (async)
        if not self.exchange_buffer:
            return

        # Filter out exchanges that lost text for some reason
        valid_exchanges = [
            ex for ex in self.exchange_buffer
            if ex.get("student_text") and ex.get("ai_text")
        ]
        if not valid_exchanges:
            logger.info("No valid exchanges to process in batch; clearing buffer")
            self.exchange_buffer.clear()
            return

        batch_size = len(valid_exchanges)
        logger.info("[MEMORY_CONSOLIDATION] Processing batch of %s exchanges for memory extraction", batch_size)
        
        try:
            # Extract memories and analysis from the batch
            # async wrapper for potentially blocking LLM call
            extraction_result = await asyncio.to_thread(
                extractor.extract_memories_batch,
                exchanges=valid_exchanges,
                student_id=self.user_id,
                session_id=self.session_id
            )
            
            # Unpack results
            extracted_memories = extraction_result.get("memories", [])
            emotions = extraction_result.get("emotions", [])
            key_moments = extraction_result.get("key_moments", [])
            unfinished_topics = extraction_result.get("unfinished_topics", [])
            
            # Update cache with analysis data
            self.cache["emotional_arc"].extend(emotions)
            self.cache["key_moments"].extend(key_moments)
            self.cache["unfinished_topics"].extend(unfinished_topics)
            
            # Save extracted memories to store (Pinecone + local)
            if extracted_memories:
                # Count by type before saving
                type_counts = {}
                for mem in extracted_memories:
                    mem_type = mem.type.value
                    type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
                
                logger.info(
                    "[MEMORY_CONSOLIDATION] Saving %s memories to store (breakdown: %s)",
                    len(extracted_memories),
                    type_counts,
                )
                # Async wrapper for vector store save (network I/O)
                await asyncio.to_thread(store.save_memories_batch, extracted_memories)
                
                # Also add to cache for session consolidation
                self.cache["new_memories"].extend(extracted_memories)
                logger.info(
                    "[MEMORY_CONSOLIDATION] Successfully saved %s memories from %s exchanges to Pinecone and local storage",
                    len(extracted_memories),
                    batch_size,
                )
            else:
                logger.info("[MEMORY_CONSOLIDATION] No memories extracted from batch of %s exchanges", batch_size)
            
            # Clear the buffer after processing
            self.exchange_buffer.clear()
            logger.info("Cleared exchange buffer")
            
            # Trigger regeneration after each batch of 3 exchanges
            # REMOVED THROTTLING: Condition 2 requires this update after every 3 exchanges
            # now = time.time()
            # last_regen = self.cache.get("last_regen_time", 0)
            # if now - last_regen >= 60:
            
            self.cache["last_regen_time"] = time.time()
            logger.info("Triggering closing cache regeneration (async)")
            # Fire and forget task
            asyncio.create_task(self.regenerate_closing_async(extractor))
            
        except Exception as e:
            logger.error(f"Error processing exchange batch: {e}", exc_info=True)
            # Clear buffer even on error to prevent memory buildup
            self.exchange_buffer.clear()
    
    async def flush_remaining_exchanges(self, extractor: MemoryExtractor, store: MemoryStore):
        """Process any remaining exchanges in buffer (called at session end)."""
        async with self._lock:
            if not self.exchange_buffer:
                logger.info("No remaining exchanges to flush")
                return
            
            remaining_count = len(self.exchange_buffer)
            logger.info("Flushing %s remaining exchanges from buffer", remaining_count)
            await self._process_exchange_batch(extractor, store)
        
        # Final regeneration at session end
        logger.info("Final closing cache regeneration at session end")
        await self.regenerate_closing_async(extractor)
    
    async def regenerate_closing_async(self, extractor: MemoryExtractor):
        """Regenerate closing cache content using LLM (non-blocking async)."""
        logger.info("Starting closing cache regeneration (consolidated async)")
        
        try:
            # Prepare context
            topics = ', '.join(self.cache["topics_covered"]) if self.cache["topics_covered"] else "general topics"
            moments = ', '.join(self.cache["key_moments"]) if self.cache["key_moments"] else "None"
            emotions = ' -> '.join(self.cache["emotional_arc"]) if self.cache["emotional_arc"] else "neutral"
            unfinished = self.cache.get("unfinished_topics", [])
            unfinished_str = ', '.join(unfinished) if unfinished else "None"
            current_emotion = self.cache["emotional_arc"][-1] if self.cache["emotional_arc"] else "neutral"

            # Execute LLM call with retry and circuit breaker logic
            data = await self._generate_closing_artifacts_call(
                topics, moments, emotions, current_emotion, unfinished_str
            )
            
            if not data:
                return

            # Update cache
            if data.get("summary"):
                self.cache["session_summary"] = data["summary"]
            if data.get("goodbye"):
                self.cache["goodbye_message"] = data["goodbye"]
            if data.get("hooks"):
                # Merge with actual unfinished topics
                generated_hooks = data["hooks"]
                final_hooks = unfinished[:2] 
                final_hooks.extend(generated_hooks[:3-len(final_hooks)])
                self.cache["next_session_hooks"] = final_hooks[:3]

            logger.info("Closing cache regeneration complete (Consolidated Async)")
            
            # Save closing cache in real-time
            await asyncio.to_thread(self._save_closing_realtime)
            
        except Exception as e:
            logger.error(f"Error in regenerate_closing_async: {e}", exc_info=True)

    @with_circuit_breaker(llm_circuit_breaker, fallback_return=None)
    @with_retry(exceptions=(Exception,), retries=2)
    async def _generate_closing_artifacts_call(self, topics, moments, emotions, current_emotion, unfinished_str):
        """Helper to make the actual LLM call, protected by decorators."""
        import google.generativeai as genai
        
        prompt = f"""Analyze this session data and generate closing artifacts.

Data:
- Topics: {topics}
- Key Moments: {moments}
- Emotional Journey: {emotions} (Ending: {current_emotion})
- Unfinished Topics: {unfinished_str}

Generate a JSON object with these 3 keys:
1. "summary": 1-2 conc sentences on what was learned and how they felt.
2. "goodbye": A warm, natural, personal goodbye message (1-2 sentences) acknowledging their emotion.
3. "hooks": Array of 2-3 specific, actionable next session limits/topics based on unfinished items or key moments.

Return ONLY valid JSON:
{{
  "summary": "...",
  "goodbye": "...",
  "hooks": ["...", "..."]
}}"""

        def _call_gemini():
            model = genai.GenerativeModel("gemini-2.0-flash-lite")
            response = model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            return json.loads(text.strip())

        # Offload blocking call to thread
        return await asyncio.to_thread(_call_gemini)

    
    def _generate_goodbye_message_sync(self) -> str:
        """Generate goodbye message based on emotional state using LLM (synchronous)."""
        import google.generativeai as genai
        
        current_emotion = self.cache["emotional_arc"][-1] if self.cache["emotional_arc"] else "neutral"
        moments = ', '.join(self.cache["key_moments"][-3:]) if self.cache["key_moments"] else "None"
        topics = ', '.join(self.cache["topics_covered"]) if self.cache["topics_covered"] else "general topics"
        
        prompt = f"""Generate a warm, natural goodbye message for a tutoring session.

Current emotional state: {current_emotion}
Key moments: {moments}
Topics covered: {topics}

Create a brief (1-2 sentences) goodbye that:
- Acknowledges their emotional state
- Encourages them appropriately
- Feels genuine and personal

Return ONLY the goodbye message, nothing else."""
        
        try:
            model = genai.GenerativeModel("gemini-2.0-flash-lite")
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"❌ Error generating goodbye_message: {e}")
            return ""
    
    def _generate_next_session_hooks_sync(self) -> list:
        """Generate next session hooks based on unfinished topics and key moments."""
        import google.generativeai as genai
        
        unfinished = self.cache.get("unfinished_topics", [])
        moments = self.cache.get("key_moments", [])
        
        # Base hooks on actual unfinished topics first
        if unfinished:
            hooks = unfinished[:3]
            # Enhance with LLM if needed for better phrasing
            if len(hooks) < 3 and moments:
                summary = self.cache.get("session_summary", "")
                prompt = f"""Based on unfinished topics and key moments, suggest 1-2 additional specific continuation topics.

Unfinished topics: {', '.join(unfinished)}
Key moments: {', '.join(moments[-3:]) if moments else 'None'}
Session summary: {summary if summary else 'Session in progress'}

Return as JSON array of strings. Each should be specific and actionable.
Example: ["Continue practicing completing the square", "Explore how discriminant relates to graph shape"]

Return ONLY the JSON array, nothing else."""
                try:
                    model = genai.GenerativeModel("gemini-2.0-flash-lite")
                    response = model.generate_content(prompt)
                    text = response.text.strip()
                    if text.startswith("```json"):
                        text = text[7:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                    additional = json.loads(text)
                    hooks.extend(additional[:3 - len(hooks)])
                except Exception:
                    pass
            return hooks[:3]
        
        # Fallback: generate from key moments if no unfinished topics
        if moments:
            summary = self.cache.get("session_summary", "")
            topics = ', '.join(self.cache.get("topics_covered", [])) or "general topics"
            prompt = f"""Based on key moments from this session, suggest 2-3 specific continuation topics.

Key moments: {', '.join(moments)}
Session summary: {summary if summary else 'Session in progress'}
Topics covered: {topics}

Return as JSON array of strings. Each should be specific and actionable.
Example: ["Continue practicing completing the square", "Explore how discriminant relates to graph shape"]

Return ONLY the JSON array, nothing else."""
            try:
                model = genai.GenerativeModel("gemini-2.0-flash-lite")
                response = model.generate_content(prompt)
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()
                return json.loads(text)
            except Exception as e:
                logger.error(f"Error generating next_session_hooks: {e}")
        
        return []
    
    def _save_closing_realtime(self):
        """Save closing cache to JSON file in real-time (called after each regeneration)."""
        try:
            data_dir = f"services/TeachingAssistant/Memory/data/{self.user_id}/memory/TeachingAssistant"
            os.makedirs(data_dir, exist_ok=True)
            
            file_path = f"{data_dir}/TA-closing-retrieval.json"
            
            # Convert Memory objects to dicts for JSON serialization
            cache_copy = self.cache.copy()
            if "new_memories" in cache_copy:
                cache_copy["new_memories"] = [
                    memory.to_dict() if hasattr(memory, 'to_dict') else memory
                    for memory in cache_copy["new_memories"]
                ]
            
            closing_data = {
                "session_id": self.session_id,
                "timestamp": time.time(),
                **cache_copy
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(closing_data, f, indent=2, ensure_ascii=False)
            
            logger.info("Saved closing cache in real-time to %s", file_path)
        except Exception as e:
            logger.error(f"Error saving closing cache in real-time: {e}", exc_info=True)


class MemoryConsolidator:
    def __init__(self, store: MemoryStore, extractor: MemoryExtractor):
        self.store = store
        self.extractor = extractor

    async def consolidate_session(self, user_id: str, session_id: str, closing_cache: SessionClosingCache):
        logger.info("[MEMORY_CONSOLIDATION] Starting session consolidation for session %s, user %s", session_id, user_id)
        
        # Flush any remaining exchanges in buffer (< 3)
        await closing_cache.flush_remaining_exchanges(self.extractor, self.store)
        
        # Count total memories generated
        total_memories = len(closing_cache.cache.get('new_memories', []))
        memory_counts = {}
        for mem in closing_cache.cache.get('new_memories', []):
            mem_type = mem.type.value if hasattr(mem, 'type') else 'unknown'
            memory_counts[mem_type] = memory_counts.get(mem_type, 0) + 1
        
        logger.info("[MEMORY_CONSOLIDATION] Total memories generated this session: %s (breakdown: %s)", 
                   total_memories, memory_counts)
        logger.info("[MEMORY_CONSOLIDATION] All memories already saved in real-time batches to Pinecone and local storage")

        logger.info(
            "[MEMORY_CONSOLIDATION] Session stats - Emotions: %s, Key moments: %s, Topics covered: %s, Unfinished topics: %s",
            len(closing_cache.cache['emotional_arc']),
            len(closing_cache.cache['key_moments']),
            len(closing_cache.cache['topics_covered']),
            len(closing_cache.cache.get('unfinished_topics', [])),
        )
        
        # Offload file I/O to thread
        await asyncio.to_thread(self._save_closing, user_id, closing_cache)
        
        # Generate opening context (LLM calls inside) in BACKGROUND to avoid blocking session end
        # This ensures the user gets the closing message immediately.
        # It also creates the hook for the next session.
        asyncio.create_task(self._generate_and_save_opening_background(user_id, closing_cache))
        
        logger.info("[MEMORY_CONSOLIDATION] Session consolidation complete for %s (Opening context generation running in background)", session_id)

    async def _generate_and_save_opening_background(self, user_id: str, closing_cache: SessionClosingCache):
        """
        Background task to generate and save opening context.
        This runs in parallel after the session is closed.
        """
        try:
            logger.info("Starting background opening context generation for user %s", user_id)
            opening_context = await self._generate_opening_context_async(user_id, closing_cache)
            await asyncio.to_thread(self._save_opening, user_id, opening_context)
            logger.info("Background opening context generation complete for user %s", user_id)
        except Exception as e:
            logger.error(f"Error in background opening context generation: {e}", exc_info=True)

    async def _generate_opening_context_async(self, user_id: str, closing_cache: SessionClosingCache) -> dict:
        """Generate personalized opening context for next session using LLM (Async wrapper)."""
        logger.info("Generating opening context (async)")
        # We can implement a similar _generate_opening_context_call protected method 
        # or just wrap the existing logic in to_thread here for simplicity in this step.
        return await asyncio.to_thread(self._generate_opening_context, user_id, closing_cache)

    def _generate_personal_relevance(self, user_id: str) -> str:
        """Generate time-contextual personal relevance string."""
        import google.generativeai as genai
        from datetime import datetime
        
        personal_memories = self.store.search(
            query="personal information about student schedule hobbies recurring events",
            student_id=user_id,
            mem_type=MemoryType.PERSONAL,
            top_k=5
        )
        
        if not personal_memories:
            return ""
        
        now = datetime.now()
        day_name = now.strftime("%A")
        time_context = "morning" if now.hour < 12 else "afternoon" if now.hour < 17 else "evening"
        personal_texts = [m["memory"].text for m in personal_memories[:3]]
        
        prompt = f"""Generate a brief, time-contextual personal relevance string (max 20 words) for a tutoring session.

Current day: {day_name}
Time of day: {time_context}
Personal memories: {', '.join(personal_texts)}

Create a natural, contextual string that references their personal life relevant to NOW.
Examples:
- "It's Friday - basketball game today?"
- "Ready for another week of learning?"
- "How's your week going?"

If no time-specific relevance, return empty string.
Return ONLY the relevance string or empty string, nothing else."""

        try:
            model = genai.GenerativeModel("gemini-2.0-flash-lite")
            response = model.generate_content(prompt)
            relevance = response.text.strip()
            return relevance if relevance and len(relevance) > 0 else ""
        except Exception as e:
            logger.error(f"❌ Error generating personal_relevance: {e}")
            return ""

    def _generate_opening_context(self, user_id: str, closing_cache: SessionClosingCache) -> dict:
        """Generate personalized opening context for next session using LLM."""
        import google.generativeai as genai
        
        model = genai.GenerativeModel("gemini-2.0-flash-lite")
        
        # Extract data from closing cache
        session_summary = closing_cache.cache.get("session_summary", "")
        emotional_arc = closing_cache.cache.get("emotional_arc", [])
        key_moments = closing_cache.cache.get("key_moments", [])
        unfinished_topics = closing_cache.cache.get("unfinished_topics", [])
        
        emotional_state_last = emotional_arc[-1] if emotional_arc else "neutral"
        
        # Generate time-contextual personal relevance
        personal_relevance = self._generate_personal_relevance(user_id)
        
        # Generate welcome_hook - reference specific achievements
        welcome_hook = ""
        if session_summary or key_moments:
            achievement = key_moments[-1] if key_moments else ""
            welcome_hook_prompt = f"""Generate a warm, natural welcome message (1-2 sentences) that references a specific achievement from last session.

Last session summary: {session_summary if session_summary else 'Previous session'}
Key achievement: {achievement if achievement else 'Session completed'}
Emotional state when they left: {emotional_state_last}

Reference the specific achievement naturally. Examples:
- "Last time you cracked the discriminant - ready to build on that?"
- "You had that breakthrough with visual diagrams - let's keep that momentum going!"

Return ONLY the welcome message, nothing else."""

            try:
                response = model.generate_content(welcome_hook_prompt)
                welcome_hook = response.text.strip()
            except Exception as e:
                logger.error(f"❌ Error generating welcome_hook: {e}")
        
        # Use actual unfinished topics from closing cache
        unfinished_threads = unfinished_topics[:3] if unfinished_topics else []
        
        # Generate suggested_opener
        suggested_opener = ""
        if session_summary or personal_relevance or unfinished_threads:
            opener_prompt = f"""Generate a natural, conversational opening line (1-2 sentences) for an AI tutor.

Last session: {session_summary if session_summary else 'Previous session completed'}
Emotional state: {emotional_state_last}
Personal context: {personal_relevance if personal_relevance else 'None'}
Unfinished topics: {', '.join(unfinished_threads[:2]) if unfinished_threads else 'None'}

Create a warm, natural conversation starter that feels genuine. Reference last session or personal life if relevant.
Sound like a friendly tutor who remembers them.

Return ONLY the opener, nothing else."""

            try:
                response = model.generate_content(opener_prompt)
                suggested_opener = response.text.strip()
            except Exception as e:
                logger.error(f"❌ Error generating suggested_opener: {e}")
        
        return {
            "welcome_hook": welcome_hook,
            "last_session_summary": session_summary,
            "unfinished_threads": unfinished_threads,
            "personal_relevance": personal_relevance,
            "emotional_state_last": emotional_state_last,
            "suggested_opener": suggested_opener
        }

    def _save_closing(self, user_id: str, closing_cache: SessionClosingCache):
        data_dir = f"services/TeachingAssistant/Memory/data/{user_id}/memory/TeachingAssistant"
        os.makedirs(data_dir, exist_ok=True)
        
        file_path = f"{data_dir}/TA-closing-retrieval.json"
        
        # Convert Memory objects to dicts for JSON serialization
        cache_copy = closing_cache.cache.copy()
        if "new_memories" in cache_copy:
            cache_copy["new_memories"] = [
                memory.to_dict() if hasattr(memory, 'to_dict') else memory
                for memory in cache_copy["new_memories"]
            ]
        
        closing_data = {
            "session_id": closing_cache.session_id,
            "timestamp": time.time(),
            **cache_copy
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(closing_data, f, indent=2, ensure_ascii=False)

    def _save_opening(self, user_id: str, opening_context: dict):
        data_dir = f"services/TeachingAssistant/Memory/data/{user_id}/memory/TeachingAssistant"
        os.makedirs(data_dir, exist_ok=True)
        
        file_path = f"{data_dir}/TA-opening-retrieval.json"
        opening_data = {
            "timestamp": time.time(),
            **opening_context
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(opening_data, f, indent=2, ensure_ascii=False)
