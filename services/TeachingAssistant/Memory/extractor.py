import os
import sys
import json
from typing import List, Optional, Dict, Any
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.logging_config import get_logger
from .schema import Memory, MemoryType

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

logger = get_logger(__name__)


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
        prompt = f"""Analyze these {len(exchanges)} conversation exchanges to update the Student Profile.

{exchanges_text}

Task 1: Extract STUDENT MEMORIES.
**GOLDEN RULE**: You are recording PERMANENT FACTS about the Student. You are NOT summarizing a conversation.

1. **STRICT PROHIBITION (Zero Tolerance)**:
   - **NEVER** mention "The AI", "The Tutor", "The System", "The Assistant", or "The Conversation".
   - **NEVER** output meta-commentary like "Student responded to the prompt" or "Student interacted with the system".
   - **BAD Example**: "Student asked the AI for help with algebra."
   - **GOOD Example**: "Student requested help with algebra."
   - **BAD Example**: "Student answered the AI correctly."
   - **GOOD Example**: "Student demonstrated mastery of [specific concept]."

2. **CRITICAL TRANSCRIPTION HANDLING (Audio Artifacts)**:
   - The "Student" text comes from realtime audio-to-text. It may contain broken words (e.g., "Cu rrent ly", "chem is try").
   - **REPAIR**: You MUST mentally repair these fragments to capture the INTENT (e.g. treat "chem is try" as "chemistry").
   - **NO META-MEMORIES**: DO NOT record memories about the text format (e.g., "Student types with spaces" -> DELETE THIS).
   - **IGNORE GARBAGE**: If text is unintelligible, IGNORE IT. Do not record "Student text is unclear".

3. **CATEGORIES**:
   - **Academic**: Knowledge gaps, misconceptions, or mastery (e.g., "Understands chain rule", "Confused by integrals").
   - **Personal**: Hobbies, life details (e.g., "Plays soccer", "Has a dog named Max").
   - **Preference**: Learning needs (e.g., "Prefers visual examples", "Dislikes long lectures").
   - **Context**: Emotional state (e.g., "Anxious about upcoming exam").

Task 2: Detect EMOTIONS (frustrated, confused, excited, anxious, tired, happy, or neutral).
Task 3: Identify KEY MOMENTS (breakthroughs, major struggles).
Task 4: Identify UNFINISHED TOPICS.

Return a SINGLE JSON object with this structure:
{{
  "memories": [
    {{
      "type": "academic|personal|preference|context",
      "text": "Fact about the student (e.g. 'Struggles with quadratic formula', ' Loves sci-fi movies')",
      "importance": 0.0-1.0,
      "metadata": {{ "emotion": "...", "topic": "..." }}
    }}
  ],
  "emotions": ["..."],
  "key_moments": ["..."],
  "unfinished_topics": ["..."]
}}

Return ONLY valid JSON.
"""

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

            # Detailed logging for memory extraction
            if len(memories) > 0:
                # Count by type
                memory_counts = {}
                for mem in memories:
                    mem_type = mem.type.value
                    memory_counts[mem_type] = memory_counts.get(mem_type, 0) + 1
                
                logger.info("[MEMORY_EXTRACTION] Extracted %s memories from %s exchanges", len(memories), len(exchanges))
                logger.info("[MEMORY_EXTRACTION] Memory breakdown: %s", memory_counts)
                
                # Log each memory with type and importance
                for i, mem in enumerate(memories, 1):
                    emotion_str = f", emotion: {mem.metadata.get('emotion', 'none')}" if mem.metadata.get('emotion') else ""
                    safe_text = mem.text.encode("ascii", "replace").decode("ascii")
                    logger.info("[MEMORY_EXTRACTION] Memory %s/%s: [%s] (importance: %.2f%s) - %s", 
                              i, len(memories), mem.type.value.upper(), mem.importance, emotion_str, safe_text[:100])
            else:
                logger.info("[MEMORY_EXTRACTION] No memories extracted from %s exchanges", len(exchanges))
                
            if result["emotions"]:
                safe_emotions = [str(e).encode("ascii", "replace").decode("ascii") for e in result["emotions"]]
                logger.info("[MEMORY_EXTRACTION] Detected emotions: %s", safe_emotions)
            if result["key_moments"]:
                safe_moments = [str(k).encode("ascii", "replace").decode("ascii") for k in result["key_moments"]]
                logger.info("[MEMORY_EXTRACTION] Key moments: %s", safe_moments)
            if result["unfinished_topics"]:
                safe_topics = [str(t).encode("ascii", "replace").decode("ascii") for t in result["unfinished_topics"]]
                logger.info("[MEMORY_EXTRACTION] Unfinished topics: %s", safe_topics)
                
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
