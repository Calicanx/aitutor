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
from google import genai
from dotenv import load_dotenv

load_dotenv()

class MemoryRetriever:
    # Memory management constants
    MAX_HISTORY_PER_SESSION = 10  # Reduced from 15
    MAX_TOTAL_SESSIONS = 50  # Global cap on concurrent sessions
    MAX_INJECTED_IDS = 100  # Sliding window for injected memory IDs
    
    def __init__(self, store: MemoryStore):
        self.store = store
        self._conversation_history: Dict[str, List[dict]] = {}
        self._turn_counts: Dict[str, int] = {}
        self._session_retrievals: Dict[str, dict] = {}
        self._injected_memory_ids: Dict[str, Set[str]] = {}
        self._lock = threading.Lock()  # Lock for thread safety
        self._session_access_times: Dict[str, float] = {}  # Track for LRU cleanup

    def on_user_turn(self, session_id: str, user_id: str, user_text: str, 
                     timestamp: float, adam_text: str = ""):
        logger = get_logger(__name__)
        
        with self._lock:
            # Initialize session if not exists
            if session_id not in self._conversation_history:
                # Check if we need to cleanup old sessions
                if len(self._conversation_history) >= self.MAX_TOTAL_SESSIONS:
                    self._cleanup_oldest_session()
                
                self._conversation_history[session_id] = []
                self._turn_counts[session_id] = 0
                self._session_retrievals[session_id] = {"light": [], "deep": {}}
                self._injected_memory_ids[session_id] = set()
                self._session_retrievals[session_id]["last_deep_time"] = time.time()
            
            # Update access time for LRU
            self._session_access_times[session_id] = time.time()

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

        # Implement rolling window - keep only last MAX_HISTORY_PER_SESSION turns
        if len(self._conversation_history[session_id]) > self.MAX_HISTORY_PER_SESSION:
            self._conversation_history[session_id] = self._conversation_history[session_id][-self.MAX_HISTORY_PER_SESSION:]
        
        # Trim injected_memory_ids to prevent unbounded growth (sliding window)
        if len(self._injected_memory_ids[session_id]) > self.MAX_INJECTED_IDS:
            # Keep only the most recent IDs
            ids_list = list(self._injected_memory_ids[session_id])
            self._injected_memory_ids[session_id] = set(ids_list[-self.MAX_INJECTED_IDS:])

        # Sanitize user_text snippet for consoles that don't support full Unicode
        snippet = (user_text or "")[:50]
        safe_snippet = snippet.encode("ascii", "ignore").decode("ascii", "ignore")

        # --- Contextual Retrieval Analysis ---
        # Instead of blindly searching for the user's raw text, we ask the LLM:
        # 1. Do we actually need to retrieve anything? (Skip for "ok", "thanks", etc.)
        # 2. If yes, what is the best search query to find relevant info?
        
        retrieval_analysis = self._analyze_retrieval_context(user_text, adam_text)
        should_retrieve = retrieval_analysis.get("need_retrieval", True)
        search_query = retrieval_analysis.get("retrieval_query", user_text)

        light_results = []
        if should_retrieve:
            logger.info(
                "[MEMORY_RETRIEVAL] Starting TA-light retrieval for session %s, user_id: %s",
                session_id,
                user_id,
            )
            # Sanitize for logging (Windows/CP1252 safety)
            safe_query = search_query.encode("ascii", "replace").decode("ascii")
            logger.info("[MEMORY_RETRIEVAL] Contextual Query: '%s' (Original: '%s')", safe_query, safe_snippet)
            logger.info("[MEMORY_RETRIEVAL] Using MemoryStore with index: %s", self.store.index_name)
            
            try:
                light_results = self.store.search(
                    query=search_query,
                    student_id=user_id,
                    top_k=10,
                    exclude_session_id=session_id
                )
            except Exception as e:
                logger.error(f"[MEMORY_RETRIEVAL] Error during search: {e}", exc_info=True)
                light_results = []
        else:
            logger.info(
                "[MEMORY_RETRIEVAL] Skipping TA-light retrieval (Analysis: retrieval not needed for '%s')", 
                safe_snippet
            )

        with self._lock:
            self._session_retrievals[session_id]["light"] = light_results
        
        if light_results:
            # Count by type
            type_counts = {}
            for r in light_results:
                mem_type = r["memory"].type.value
                type_counts[mem_type] = type_counts.get(mem_type, 0) + 1
            
            # ===== DETAILED LOGGING: Retrieved Memories =====
            logger.info("╔" + "═" * 78 + "╗")
            logger.info("║ [LIGHT RETRIEVAL] Found %s memories (breakdown: %s)%s║" % (
                len(light_results), 
                type_counts,
                " " * (78 - 48 - len(str(len(light_results))) - len(str(type_counts)))
            ))
            logger.info("╠" + "═" * 78 + "╣")
            
            for i, r in enumerate(light_results, 1):
                # Get safe text for logging
                safe_text = r["memory"].text.encode("ascii", "replace").decode("ascii")
                emotion = r['memory'].metadata.get('emotion', 'none')
                mem_type = r["memory"].type.value.upper()
                score = r["score"]
                
                logger.info("║ Memory #%d%s║" % (i, " " * (76 - 10)))
                logger.info("║ ├─ Type: %s%s║" % (mem_type, " " * (78 - 10 - len(mem_type))))
                logger.info("║ ├─ Score: %.4f (similarity)%s║" % (score, " " * (78 - 28)))
                logger.info("║ ├─ Emotion: %s%s║" % (emotion, " " * (78 - 13 - len(emotion))))
                logger.info("║ └─ Text: %s%s║" % (
                    safe_text[:62] if len(safe_text) > 62 else safe_text,
                    " " * max(0, 78 - 11 - min(len(safe_text), 62))
                ))
                
                # If text is longer, continue on next lines
                if len(safe_text) > 62:
                    remaining = safe_text[62:]
                    for j in range(0, len(remaining), 68):
                        chunk = remaining[j:j+68]
                        logger.info("║          %s%s║" % (chunk, " " * (68 - len(chunk))))
                
                if i < len(light_results):
                    logger.info("║%s║" % (" " * 78))
            
            logger.info("╚" + "═" * 78 + "╝")
            # ================================================
        else:
            logger.info("[MEMORY_RETRIEVAL] No memories found for query: %s...", safe_snippet)
        self._save_retrieval(session_id, user_id, "light", light_results)

        current_time = time.time()
        
        # Safely access session data (could be cleared by concurrent thread)
        session_data = self._session_retrievals.get(session_id)
        if session_data:
            last_deep = session_data.get("last_deep_time", 0)
            if current_time - last_deep >= 180:
                self._do_deep_retrieval(session_id, user_id)
                
                # Update time safely
                with self._lock:
                    if session_id in self._session_retrievals:
                        self._session_retrievals[session_id]["last_deep_time"] = current_time
    
    def _cleanup_oldest_session(self):
        """Remove the least recently used session to free memory"""
        if not self._session_access_times:
            return
        
        # Find oldest session
        oldest_session = min(self._session_access_times.items(), key=lambda x: x[1])[0]
        
        logger.info(f"[MEMORY_RETRIEVAL] Cleaning up oldest session {oldest_session} to free memory (LRU eviction)")
        
        # Clean up all associated data
        if oldest_session in self._conversation_history:
            del self._conversation_history[oldest_session]
        if oldest_session in self._turn_counts:
            del self._turn_counts[oldest_session]
        if oldest_session in self._session_retrievals:
            del self._session_retrievals[oldest_session]
        if oldest_session in self._injected_memory_ids:
            del self._injected_memory_ids[oldest_session]
        if oldest_session in self._session_access_times:
            del self._session_access_times[oldest_session]


    def _analyze_deep_retrieval_context(self, conversation_text: str) -> str:
        """
        Generate a search query for Deep Retrieval based on recent conversation history.
        Always runs to synthesize themes.
        """
        logger = get_logger(__name__)
        
        # Fallback to raw text if analysis fails
        fallback_query = conversation_text

        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            
            # Truncate context if too long
            safe_context = conversation_text[:2000]

            prompt = f"""You are an Expert Knowledge Synthesizer for an AI Tutor.
            Analyze the recent conversation history (last few minutes) to generate a Deep Search Query.

            Context: "{safe_context}"

            GOAL:
            Identify the **underlying themes**, **concepts**, or **patterns** that require checking long-term memory.
            We are NOT looking for exact keyword matches of what was just said. We are looking for **related past experiences**.

            INSTRUCTIONS:
            1. Identify the core academic topic (e.g., "quadratic equations").
            2. Identify the student's current state/struggle (e.g., "confused about variables").
            3. Identify any personal hooks mentioned (e.g., "basketball analogy").
            
            GENERATE A SINGLE SEARCH STRING that combines:
            - The Academic Concept
            - The Type of Struggle/Interaction
            - Potential Personal Connections

            EXAMPLE:
            Context: "I just don't get why t is negative. It's like the ball is going underground."
            Bad Query: "t is negative ball underground"
            Good Query: "negative variables logic physics trajectory misconceptions basketball analogies"

            Return strict JSON:
            {{
                "deep_query": "string"
            }}
            """
            
            # ===== LOGGING: Deep Retrieval Analysis =====
            try:
                logger.info("┌" + "─" * 78 + "┐")
                logger.info("│ [DEEP RETRIEVAL ANALYSIS] LLM Call for Query Generation" + " " * 21 + "│")
                logger.info("└" + "─" * 78 + "┘")
            except Exception:
                pass
            # ===========================================

            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            result = json.loads(text.strip())
            deep_query = result.get("deep_query", conversation_text)

            # ===== LOGGING: Deep Query Result =====
            try:
                logger.info("┌" + "─" * 78 + "┐")
                logger.info("│ [DEEP QUERY GENERATED]" + " " * 54 + "│")
                logger.info("├" + "─" * 78 + "┤")
                logger.info(f"│ Query: {deep_query[:69]:<69} │")
                if len(deep_query) > 69:
                    logger.info(f"│        {deep_query[69:138]:<69} │")
                logger.info("└" + "─" * 78 + "┘")
            except Exception:
                pass
            # ======================================

            return deep_query

        except Exception as e:
            logger.warning(f"[DEEP RETRIEVAL ANALYSIS] Error, using raw text: {e}")
            return fallback_query

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
        
        # === ENHANCEMENT: Use LLM to generate the deep search query ===
        deep_search_query = self._analyze_deep_retrieval_context(conversation_text)
        
        convo_snippet = (deep_search_query or "")[:100]
        convo_safe = convo_snippet.encode("ascii", "ignore").decode("ascii", "ignore")
        logger.info("[MEMORY_RETRIEVAL] Using Optimized Deep Query: %s...", convo_safe)
        
        deep_results = {}
        total_results = 0
        
        # Optimize: Parallelize Pinecone searches (reduction ~4x latency)
        # Check if deep_search_query is valid
        if not deep_search_query or not deep_search_query.strip():
            logger.warning("[MEMORY_RETRIEVAL] Deep search query is empty, skipping deep retrieval.")
            return

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_type = {
                executor.submit(
                    self.store.search,
                    query=deep_search_query,     # Use the optimized query here!
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
        
        # ===== DETAILED LOGGING: Deep Retrieval Results =====
        type_breakdown = {mem_type: len(results) for mem_type, results in deep_results.items()}
        logger.info("╔" + "═" * 78 + "╗")
        logger.info("║ [DEEP RETRIEVAL] Found %s total memories (breakdown: %s)%s║" % (
            total_results,
            type_breakdown,
            " " * max(0, 78 - 50 - len(str(total_results)) - len(str(type_breakdown)))
        ))
        logger.info("╠" + "═" * 78 + "╣")
        
        # Log all memories by type with detailed information
        for mem_type, results in deep_results.items():
            if results:
                logger.info("║ %s%s║" % (" " * 78, ""))
                logger.info("║ ┌─ %s (%s memories)%s║" % (
                    mem_type.upper(),
                    len(results),
                    " " * max(0, 78 - 7 - len(mem_type) - len(str(len(results))) - 11)
                ))
                logger.info("║ │%s║" % (" " * 78))
                
                for i, r in enumerate(results, 1):
                    safe_text = r["memory"].text.encode("ascii", "replace").decode("ascii")
                    score = r["score"]
                    emotion = r["memory"].metadata.get("emotion", "none")
                    
                    logger.info("║ │  Memory #%d%s║" % (i, " " * (78 - 13)))
                    logger.info("║ │  ├─ Score: %.4f%s║" % (score, " " * (78 - 18)))
                    logger.info("║ │  ├─ Emotion: %s%s║" % (emotion, " " * (78 - 16 - len(emotion))))
                    logger.info("║ │  └─ Text: %s%s║" % (
                        safe_text[:59] if len(safe_text) > 59 else safe_text,
                        " " * max(0, 78 - 14 - min(len(safe_text), 59))
                    ))
                    
                    # Continue text on next lines if needed
                    if len(safe_text) > 59:
                        remaining = safe_text[59:]
                        for j in range(0, len(remaining), 65):
                            chunk = remaining[j:j+65]
                            logger.info("║ │           %s%s║" % (chunk, " " * (65 - len(chunk))))
                    
                    if i < len(results):
                        logger.info("║ │%s║" % (" " * 78))
        
        logger.info("╚" + "═" * 78 + "╝")
        # ====================================================
        
        self._save_retrieval(session_id, user_id, "deep", deep_results)

    def _synthesize_instruction(self, memories: list, conversation_context: str) -> Optional[str]:
        """Use LLM to synthesize memories into actionable instruction"""
        logger = get_logger(__name__)
        
        if not memories:
            return None
        
        # Format memories for LLM
        memory_texts = [f"- {m['memory'].text}" for m in memories]
        memories_str = "\n".join(memory_texts)
        
        prompt = f"""You are a reflection layer for an AI tutor system.

Retrieved Memories:
{memories_str}

Recent Conversation Context:
{conversation_context}

TASK: Synthesize these memories into a SINGLE actionable instruction for the tutor.
- Only return an instruction if memories are highly relevant to current conversation
- Make it specific and actionable
- Focus on HOW the tutor should adapt their teaching based on these memories

Return ONLY the instruction text, or "NONE" if memories aren't relevant enough.

Examples:
- "Student prefers visual diagrams - use a visual approach for this concept"
- "Student struggled with negative numbers last time - check understanding before proceeding"
- "Student gets frustrated with algebra - provide extra encouragement and break into smaller steps"
"""
        
        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt
            )
            instruction = response.text.strip()
            
            if instruction.upper() == "NONE" or not instruction:
                logger.info("[REFLECTION] No relevant instruction synthesized from memories")
                return None
            
            logger.info(f"[REFLECTION] Synthesized instruction: {instruction[:100]}...")
            return instruction
        except Exception as e:
            logger.error(f"[REFLECTION] Error in reflection synthesis: {e}")
            return None
    
    def get_memory_injection(self, session_id: str) -> Optional[str]:
        logger = get_logger(__name__)  # Initialize logger
        
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
        
        # Get conversation context for reflection
        conversation_context = ""
        if session_id in self._conversation_history:
            recent_turns = self._conversation_history[session_id][-3:]
            conversation_context = "\n".join([f"{t['speaker']}: {t['text']}" for t in recent_turns])
        
        # REFLECTION LAYER - Synthesize instruction from memories
        instruction = self._synthesize_instruction(memories_to_inject, conversation_context)
        
        if not instruction:
            logger.info("[MEMORY_INJECTION] Reflection layer returned no relevant instruction")
            return None
        
        # Format as system instruction
        injection_text = f"""[SYSTEM INSTRUCTION]

{instruction}

Note: This instruction is based on retrieved memories from previous sessions.
Apply it naturally without explicitly mentioning these memories to the student."""
        
        # CRITICAL FIX: Clear retrieval results after injection to free memory
        with self._lock:
            if session_id in self._session_retrievals:
                # Keep only the structure, clear the actual results
                self._session_retrievals[session_id]["light"] = []
                self._session_retrievals[session_id]["deep"] = {}
                logger.debug(f"[MEMORY_RETRIEVAL] Cleared retrieval results for session {session_id} after injection")
        
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

    def _analyze_retrieval_context(self, user_text: str, model_text: str) -> dict:
        """
        Analyze conversation context to determine if retrieval is needed and generate an optimized query.
        Uses a lightweight LLM call.
        """
        logger = get_logger(__name__)
        
        if not user_text or not user_text.strip():
            return {"need_retrieval": False, "retrieval_query": ""}

        # Default fallback
        fallback_result = {"need_retrieval": True, "retrieval_query": user_text}

        try:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            
            # Truncate for prompt safety
            safe_user = user_text[:500]
            safe_model = model_text[:500] if model_text else "Startup/Greeting"

            prompt = f"""You are an efficient Retrieval Augmented Generation (RAG) optimizer.
            Analyze the conversation turn to decide precise memory retrieval needs.

            Previous AI: "{safe_model}"
            User Input: "{safe_user}"

            TASK 1: DECISION (need_retrieval)
            - FALSE if: 
                - Simple agreement/acknowledgment ("ok", "got it", "cool", "thanks").
                - Phatic expressions or greetings ("hard to say", "wow", "hi").
                - Rhetorical questions or emotional reactions without specific factual content.
            - TRUE if: 
                - Direct questions or requests for explanation.
                - Statements of confusion ("I don't get the quadratic formula").
                - Explicit statements of preference ("I hate reading").
                - Personal disclosures ("I play basketball").
                - Domain-specific terms that might need definition.

            TASK 2: QUERY GENERATION (retrieval_query)
            - If decision is TRUE, generate a **keyword-focused** search query.
            - REMOVE: "student says", "user wants to know", "retrieval for".
            - FOCUS ON: Core entities, concepts, and specific gaps.
            - EXAMPLE: User says "I don't get the discriminant". Query: "discriminant definition purpose quadratic formula explanation"
            - EXAMPLE: User says "My math teacher is strict". Query: "math teacher relationship classroom environment academic pressure"
            
            Return strict JSON:
            {{
                "need_retrieval": true/false,
                "retrieval_query": "string",
                "reasoning": "brief explanation"
            }}
            """
            
            # ===== DETAILED LOGGING: LLM Retrieval Analysis =====
            # Wrap in try-except to prevent logging errors from breaking retrieval
            try:
                logger.info("┌" + "─" * 78 + "┐")
                logger.info("│ [LIGHT RETRIEVAL ANALYSIS] LLM Call" + " " * 41 + "│")
                logger.info("├" + "─" * 78 + "┤")
                logger.info(f"│ User Input: {safe_user[:60]:<60} │")
                logger.info("└" + "─" * 78 + "┘")
            except Exception:
                pass
            # ====================================================

            response = client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.endswith("```"):
                text = text[:-3]
            
            result = json.loads(text.strip())
            
            # ===== DETAILED LOGGING: LLM Decision =====
            try:
                need_retrieval = result.get("need_retrieval", True)
                retrieval_query = result.get("retrieval_query", user_text) or user_text
                reasoning = result.get("reasoning", "No reasoning provided") or "No reasoning provided"
                
                logger.info("┌" + "─" * 78 + "┐")
                logger.info("│ [LIGHT RETRIEVAL DECISION] Result" + " " * 43 + "│")
                logger.info("├" + "─" * 78 + "┤")
                logger.info(f"│ Decision: {'✓ RETRIEVE' if need_retrieval else '✗ SKIP':<67} │")
                
                if need_retrieval:
                    logger.info(f"│ Query: {retrieval_query[:69]:<69} │")
                    if len(retrieval_query) > 69:
                        logger.info(f"│        {retrieval_query[69:138]:<69} │")
                else:
                    logger.info(f"│ Query: N/A (skipping retrieval){' ' * 42}│")
                
                logger.info(f"│ Reasoning: {reasoning[:65]:<65} │")
                logger.info("└" + "─" * 78 + "┘")
            except Exception as log_err:
                logger.debug(f"[RETRIEVAL ANALYSIS] Logging error: {log_err}")
            # ==========================================
            
            # minimal validation
            if "need_retrieval" in result:
                if "retrieval_query" not in result or result["retrieval_query"] is None:
                    result["retrieval_query"] = user_text
                return result
            return fallback_result

        except Exception as e:
            logger.warning(f"[RETRIEVAL ANALYSIS] Error in context analysis, using fallback: {e}")
            logger.info(f"[RETRIEVAL ANALYSIS] Fallback: need_retrieval=True, query={user_text[:50]}...")
            return fallback_result


    
