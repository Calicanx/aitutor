"""
Greeting Handler for TeachingAssistant
Generates greeting/closing prompts with optional memory awareness.
Session timing is handled by SessionManager in MongoDB.
"""

import os
import json
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GreetingHandler:
    """
    Generates greeting/closing prompts with optional memory awareness.
    Session timing is handled by SessionManager in MongoDB.
    """
    SYSTEM_PROMPT_PREFIX = "[SYSTEM PROMPT FOR ADAM]"

    def get_greeting(self, user_id: str) -> str:
        """Generate greeting prompt for session start (backward compatibility)"""
        return f"""{self.SYSTEM_PROMPT_PREFIX}
You are starting a tutoring session.
Please greet the student warmly and ask how they're doing today.
Make them feel welcome and excited to learn."""

    def start_session(self, user_id: str, session_id: str) -> str:
        """Generate memory-aware greeting prompt for session start"""
        opening = self._load_opening(user_id)
        
        # Clear opening cache after loading (so it's fresh for next session)
        self._clear_opening_cache(user_id)
        
        if opening:
            welcome = opening.get("welcome_hook", "")
            last_summary = opening.get("last_session_summary", "")
            unfinished = opening.get("unfinished_threads", [])
            personal = opening.get("personal_relevance", [])
            
            # If welcome_hook is empty (LLM failed or cleared), use fallback
            if not welcome:
                return self.get_greeting(user_id)
            
            greeting_parts = [welcome]
            if last_summary:
                greeting_parts.append(f"Last time we worked on: {last_summary}")
            if unfinished:
                greeting_parts.append(f"Unfinished topics: {', '.join(unfinished)}")
            if personal:
                greeting_parts.append("Personal context available.")
            
            return f"{self.SYSTEM_PROMPT_PREFIX}\n" + " ".join(greeting_parts)
        return self.get_greeting(user_id)

    def get_closing(self, duration_minutes: float, questions_answered: int) -> str:
        """Generate closing prompt with session stats (backward compatibility)"""
        return f"""{self.SYSTEM_PROMPT_PREFIX}
The tutoring session is ending now.
Session stats: {duration_minutes:.1f} minutes, {questions_answered} questions attempted.
Please give the student a warm closing message, acknowledge their hard work,
and encourage them for next session."""

    def end_session(self, user_id: str, session_id: str) -> str:
        """Generate memory-aware closing prompt for session end"""
        closing = self._load_closing(user_id, session_id)
        if closing:
            goodbye = closing.get("goodbye_message", "Goodbye!")
            next_hooks = closing.get("next_session_hooks", [])
            
            closing_parts = [goodbye]
            if next_hooks:
                closing_parts.append(f"Next time: {', '.join(next_hooks)}")
            
            return f"{self.SYSTEM_PROMPT_PREFIX}\n" + " ".join(closing_parts)
        return self.get_closing(0, 0)  # Fallback

    def get_inactivity_prompt(self) -> str:
        """Generate inactivity check prompt"""
        return f"""{self.SYSTEM_PROMPT_PREFIX}
Check with the student if they're there, and if they want to continue...
We have some very interesting problems to solve."""

    def _load_opening(self, user_id: str) -> Optional[dict]:
        """Load opening data from memory retrieval file"""
        file_path = f"services/TeachingAssistant/Memory/data/{user_id}/memory/TeachingAssistant/TA-opening-retrieval.json"
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load opening data: {e}")
        return None

    def _load_closing(self, user_id: str, session_id: str) -> Optional[dict]:
        """Load closing data from memory retrieval file"""
        file_path = f"services/TeachingAssistant/Memory/data/{user_id}/memory/TeachingAssistant/TA-closing-retrieval.json"
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get("session_id") == session_id:
                        return data
            except Exception as e:
                logger.warning(f"Failed to load closing data: {e}")
        return None
    
    def _clear_opening_cache(self, user_id: str):
        """Clear opening cache after it's been used for greeting"""
        try:
            file_path = f"services/TeachingAssistant/Memory/data/{user_id}/memory/TeachingAssistant/TA-opening-retrieval.json"
            if os.path.exists(file_path):
                # Initialize with empty structure
                opening_data = {
                    "timestamp": time.time(),
                    "welcome_hook": "",
                    "last_session_summary": "",
                    "unfinished_threads": [],
                    "personal_relevance": [],
                    "emotional_state_last": "neutral",
                    "suggested_opener": ""
                }
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(opening_data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"Cleared opening cache after use for user: {user_id}")
        except Exception as e:
            logger.error(f"Error clearing opening cache: {e}")
