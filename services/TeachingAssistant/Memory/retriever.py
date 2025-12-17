import os
import sys
import json
import time
import threading
from typing import Dict, List, Set, Optional
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from shared.logging_config import get_logger
from .schema import Memory, MemoryType
from .vector_store import MemoryStore

class MemoryRetriever:
    def __init__(self, store: MemoryStore):
        self.store = store
        self._conversation_history: Dict[str, List[dict]] = {}
        self._turn_counts: Dict[str, int] = {}
        self._session_retrievals: Dict[str, dict] = {}
        self._injected_memory_ids: Dict[str, Set[str]] = {}
        self._lock = threading.Lock()  # Lock for thread safety

    def on_user_turn(self, session_id: str, user_id: str, user_text: str, 
                     timestamp: float, adam_text: str = ""):
        logger = get_logger(__name__)
        
        with self._lock:
            if session_id not in self._conversation_history:
                self._conversation_history[session_id] = []
                self._turn_counts[session_id] = 0
                self._session_retrievals[session_id] = {"light": [], "deep": {}}
                self._injected_memory_ids[session_id] = set()
                self._session_retrievals[session_id]["last_deep_time"] = time.time()

            self._turn_counts[session_id] += 1
            self._conversation_history[session_id].append({
                "speaker": "user",
                "text": user_text,
                "timestamp": timestamp
            })
            if adam_text:
                self._conversation_history[session_id].append({
                    "speaker": "adam",
                    "text": adam_text,
                    "timestamp": timestamp
                })

            if len(self._conversation_history[session_id]) > 15:
                self._conversation_history[session_id] = self._conversation_history[session_id][-15:]

        # Sanitize user_text snippet for consoles that don't support full Unicode
        snippet = (user_text or "")[:50]
        safe_snippet = snippet.encode("ascii", "ignore").decode("ascii", "ignore")
        logger.info(
            "[MEMORY_RETRIEVAL] Starting TA-light retrieval for session %s, user_id: %s, query: %s...",
            session_id,
            user_id,
            safe_snippet,
        )
        logger.info("[MEMORY_RETRIEVAL] Using MemoryStore with index: %s", self.store.index_name)
        light_results = self.store.search(
            query=user_text,
            student_id=user_id,
            top_k=10,
            exclude_session_id=session_id
        )
        with self._lock:
            self._session_retrievals[session_id]["light"] = light_results
        
        if light_results:
            # Count by type
            type_counts = {}
            for r in light_results:
                mem_type = r["memory"].type.value
                type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
            
            logger.info("[MEMORY_RETRIEVAL] Found %s memories (breakdown: %s)", len(light_results), type_counts)
            logger.info("[MEMORY_RETRIEVAL] Top memories:")
            for i, r in enumerate(light_results[:5], 1):  # Show top 5
                # Sanitize text for logging to prevent UnicodeEncodeError
                safe_text = r["memory"].text.encode("ascii", "replace").decode("ascii")
                emotion_str = f", emotion: {r['memory'].metadata.get('emotion', 'none')}" if r['memory'].metadata.get('emotion') else ""
                logger.info(
                    "[MEMORY_RETRIEVAL]   %s. [%s] (score: %.3f%s) - %s",
                    i,
                    r["memory"].type.value.upper(),
                    r["score"],
                    emotion_str,
                    safe_text[:80],
                )
            if len(light_results) > 5:
                logger.info("[MEMORY_RETRIEVAL]   ... and %s more memories", len(light_results) - 5)
        else:
            logger.info("[MEMORY_RETRIEVAL] No memories found for query: %s...", safe_snippet)
        self._save_retrieval(session_id, user_id, "light", light_results)

        current_time = time.time()
        last_deep = self._session_retrievals[session_id].get("last_deep_time", 0)
        if current_time - last_deep >= 180:
            self._do_deep_retrieval(session_id, user_id)
            self._session_retrievals[session_id]["last_deep_time"] = current_time

    def _do_deep_retrieval(self, session_id: str, user_id: str):
        from concurrent.futures import ThreadPoolExecutor, as_completed
        logger = get_logger(__name__)
        
        with self._lock:
            history = self._conversation_history.get(session_id, [])
            # Create a copy of the list to use outside the lock
            recent_turns = list(history[-10:]) if len(history) >= 10 else list(history)
            
        conversation_text = " ".join([turn["text"] for turn in recent_turns])
        
        logger.info(
            "[MEMORY_RETRIEVAL] Starting TA-deep retrieval for session %s (3+ minutes since last deep retrieval)",
            session_id,
        )
        logger.info("[MEMORY_RETRIEVAL] Using MemoryStore with index: %s", self.store.index_name)
        convo_snippet = (conversation_text or "")[:100]
        convo_safe = convo_snippet.encode("ascii", "ignore").decode("ascii", "ignore")
        logger.info("[MEMORY_RETRIEVAL] Conversation context: %s...", convo_safe)
        
        deep_results = {}
        total_results = 0
        
        # Optimize: Parallelize Pinecone searches (reduction ~4x latency)
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_type = {
                executor.submit(
                    self.store.search,
                    query=conversation_text,
                    student_id=user_id,
                    mem_type=mem_type,
                    top_k=5 if mem_type == MemoryType.ACADEMIC else 3,
                    exclude_session_id=session_id
                ): mem_type
                for mem_type in MemoryType
            }
            
            for future in as_completed(future_to_type):
                mem_type = future_to_type[future]
                try:
                    results = future.result()
                    deep_results[mem_type.value] = results
                    total_results += len(results)
                except Exception as e:
                    logger.error(f"Error in deep retrieval for {mem_type.value}: {e}")
                    deep_results[mem_type.value] = []

        with self._lock:
            self._session_retrievals[session_id]["deep"] = deep_results
        
        # Log detailed breakdown
        type_breakdown = {mem_type.value: len(results) for mem_type, results in deep_results.items()}
        logger.info("[MEMORY_RETRIEVAL] TA-deep retrieval found %s total memories (breakdown: %s)", total_results, type_breakdown)
        
        # Log top memories by type
        for mem_type, results in deep_results.items():
            if results:
                logger.info("[MEMORY_RETRIEVAL]   %s: %s memories", mem_type.upper(), len(results))
                for i, r in enumerate(results[:2], 1):  # Show top 2 per type
                    safe_text = r["memory"].text.encode("ascii", "replace").decode("ascii")
                    logger.info("[MEMORY_RETRIEVAL]     %s. (score: %.3f) - %s", i, r["score"], safe_text[:60])
        
        self._save_retrieval(session_id, user_id, "deep", deep_results)
    
    def get_memory_injection(self, session_id: str) -> Optional[str]:
        if session_id not in self._session_retrievals:
            return None
        
        with self._lock:
            retrievals = self._session_retrievals.get(session_id, {})
            # Make copies to work with outside lock
            light_results = list(retrievals.get("light", []))
            deep_results = retrievals.get("deep", {}).copy()
            injected_ids = self._injected_memory_ids[session_id]
        
        memories_to_inject = []
        for result in light_results:
            mem_id = result["memory"].id
            if mem_id not in injected_ids:
                memories_to_inject.append(result)
                injected_ids.add(mem_id)

        for mem_type in MemoryType:
            for result in deep_results.get(mem_type.value, []):
                mem_id = result["memory"].id
                if mem_id not in injected_ids:
                    memories_to_inject.append(result)
                    injected_ids.add(mem_id)
        
        if not memories_to_inject:
            return None
        
        memories_by_type = {}
        for result in memories_to_inject:
            mem_type = result["memory"].type.value
            if mem_type not in memories_by_type:
                memories_by_type[mem_type] = []
            memories_by_type[mem_type].append(result["memory"])

        formatted_parts = []
        type_names = {
            "academic": "Academic Memories",
            "personal": "Personal Memories",
            "preference": "Preference Memories",
            "context": "Context Memories"
        }

        for mem_type, mems in memories_by_type.items():
            formatted_parts.append(f"{type_names.get(mem_type, mem_type.title())}:")
            for mem in mems:
                emotion = mem.metadata.get("emotion", "")
                emotion_str = f" (emotion: {emotion})" if emotion else ""
                formatted_parts.append(f"- {mem.text}{emotion_str}")

        formatted_memories = "\n".join(formatted_parts)

        injection_text = f"""{{{{SYSTEM UPDATE: RELEVANT MEMORIES RETRIEVED.

{formatted_memories}

CRITICAL INSTRUCTION:
- If you were about to reply to the user, use these memories to guide your response naturally.
- If you have JUST replied to the user and this update arrived late:
  1. DO NOT change the topic or ask a new question.
  2. If your previous reply is still valid, REPEAT it or rephrase it slightly to be consistent with these memories.
  3. DO NOT continue the conversation further than your last reply.
- Do not mention these memories explicitly in your public response. Treat them as internal context only.
}}}}"""
        
        return injection_text
    
    def _save_retrieval(self, session_id: str, user_id: str, retrieval_type: str, results):
        """Save retrieval results to JSON file. Handles both list (light) and dict (deep) results."""
        logger = get_logger(__name__)
        
        data_dir = f"services/TeachingAssistant/Memory/data/{user_id}/memory/TeachingAssistant"
        os.makedirs(data_dir, exist_ok=True)
        
        file_path = f"{data_dir}/TA-{retrieval_type}-retrieval.json"
        retrievals = []
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    retrievals = json.load(f)
            except (json.JSONDecodeError, ValueError):
                logger.warning(
                    "Could not parse %s, starting fresh",
                    file_path,
                )
                retrievals = []
        
        # Handle different result formats: list (light) or dict (deep)
        if isinstance(results, list):
            # Light retrieval: results is a list of dicts with "memory" and "score"
            results_data = [{"memory": r["memory"].to_dict(), "score": r["score"]} for r in results]
        elif isinstance(results, dict):
            # Deep retrieval: results is a dict of {memory_type: [results]}
            results_data = {}
            for mem_type, mem_results in results.items():
                results_data[mem_type] = [{"memory": r["memory"].to_dict(), "score": r["score"]} for r in mem_results]
        else:
            logger.error("Unknown results format: %s", type(results))
            results_data = []
        
        retrieval_data = {
            "session_id": session_id,
            "timestamp": time.time(),
            "results": results_data
        }
        retrievals.append(retrieval_data)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(retrievals, f, indent=2, ensure_ascii=False)
            result_count = (
                len(results)
                if isinstance(results, list)
                else sum(len(v) for v in results.values())
                if isinstance(results, dict)
                else 0
            )
            logger.info(
                "[MEMORY_RETRIEVAL] Saved %s retrieval to %s (%s results)",
                retrieval_type,
                file_path,
                result_count,
            )
        except Exception as e:
            logger.error(
                "Error saving %s retrieval: %s",
                retrieval_type,
                e,
                exc_info=True,
            )

    def clear_session(self, session_id: str):
        if session_id in self._conversation_history:
            del self._conversation_history[session_id]
        if session_id in self._turn_counts:
            del self._turn_counts[session_id]
        if session_id in self._session_retrievals:
            del self._session_retrievals[session_id]
        if session_id in self._injected_memory_ids:
            del self._injected_memory_ids[session_id]
    
