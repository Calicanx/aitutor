import os
import json
import logging
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv
from .schema import Memory, MemoryType

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

logger = logging.getLogger(__name__)


class MemoryExtractor:
    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.0-flash-lite")

    def extract_memories_batch(self, exchanges: List[Dict], student_id: str, session_id: str) -> Dict[str, Any]:
        """
        Extract memories and analyze exchanges in a single batch call.
        
        Args:
            exchanges: List of dicts with keys 'student_text', 'ai_text', 'topic'
            student_id: Student ID
            session_id: Session ID
            
        Returns:
            Dict containing:
            - memories: List of Memory objects
            - emotions: List of detected emotions
            - key_moments: List of key moments
            - unfinished_topics: List of unfinished topics
        """
        if not exchanges:
            logger.warning("extract_memories_batch called with empty exchanges list")
            return {"memories": [], "emotions": [], "key_moments": [], "unfinished_topics": []}

        logger.info(
            "Extracting memories and analyzing batch of %s exchanges for session %s",
            len(exchanges),
            session_id,
        )
        
        # Build the exchanges text for the prompt
        exchanges_text = ""
        for i, exchange in enumerate(exchanges, 1):
            exchanges_text += f"\n--- Exchange {i} ---\n"
            exchanges_text += f"Student: {exchange['student_text']}\n"
            exchanges_text += f"AI: {exchange['ai_text']}\n"
            exchanges_text += f"Topic: {exchange['topic']}\n"
        
        prompt = f"""Analyze these {len(exchanges)} conversation exchanges to extract memories and tracking data.

{exchanges_text}

Task 1: Extract MEMORIES (academic, personal, preference, context) worth remembering.
Task 2: Detect EMOTIONS (frustrated, confused, excited, anxious, tired, happy, or neutral) for each exchange.
Task 3: Identify KEY MOMENTS (breakthroughs, struggles, important events) - max 1 per exchange.
Task 4: Identify UNFINISHED TOPICS that should continue next time.

Return a SINGLE JSON object with this structure:
{{
  "memories": [
    {{
      "type": "academic|personal|preference|context",
      "text": "memorable detail",
      "importance": 0.0-1.0,
      "metadata": {{ "emotion": "...", "topic": "..." }}
    }}
  ],
  "emotions": ["emotion1", "emotion2", ...],
  "key_moments": ["moment description 1", ...],
  "unfinished_topics": ["topic description 1", ...]
}}

Select best fitting emotion for each exchange (or "neutral").
Only include key moments and unfinished topics if they are significant.
Return ONLY valid JSON."""

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            data = json.loads(text)
            
            # Process memories
            memories = []
            for item in data.get("memories", []):
                memory = Memory(
                    type=MemoryType(item.get("type", "academic")),
                    text=item.get("text", ""),
                    importance=float(item.get("importance", 0.5)),
                    student_id=student_id,
                    session_id=session_id,
                    metadata=item.get("metadata", {})
                )
                memories.append(memory)
                
            result = {
                "memories": memories,
                "emotions": [e for e in data.get("emotions", []) if e and e != "neutral"],
                "key_moments": [k for k in data.get("key_moments", []) if k and k != "None"],
                "unfinished_topics": [t for t in data.get("unfinished_topics", []) if t and t != "None"]
            }

            if len(memories) > 0:
                logger.info("   MEMORIES: %s", len(memories))
            if result["emotions"]:
                logger.info("   EMOTIONS: %s", result["emotions"])
            if result["key_moments"]:
                logger.info("   KEY MOMENTS: %s", result["key_moments"])
                
            return result
            
        except json.JSONDecodeError as e:
            logger.error("JSON decode error in batch memory extraction: %s", e)
            return {"memories": [], "emotions": [], "key_moments": [], "unfinished_topics": []}
        except Exception as e:
            logger.error("Error extracting memories from batch: %s", e, exc_info=True)
            return {"memories": [], "emotions": [], "key_moments": [], "unfinished_topics": []}

    def detect_emotion(self, text: str) -> Optional[str]:
        # Deprecated: Included in extract_memories_batch
        return None

    def detect_key_moments(self, student_text: str, ai_text: str, topic: str) -> Optional[str]:
        # Deprecated: Included in extract_memories_batch
        return None
            
    def detect_unfinished_topics(self, student_text: str, ai_text: str) -> Optional[str]:
        # Deprecated: Included in extract_memories_batch
        return None
