"""
Teaching Assistant - Enhanced with Memory, Skills, and Event Processing
All session state is stored in MongoDB via SessionManager.
Integrates memory management, skills system, and event-driven processing.
"""

import asyncio
import time
from typing import Optional, Dict, Any

from .greeting_handler import GreetingHandler
from .session_manager import SessionManager
from .core.context_manager import ContextManager
from .core.event_processor import EventProcessor
from .handlers.queue_manager import EventQueueManager
from .handlers.injection_manager import InjectionManager
from .skills_manager import SkillsManager
from .Memory.vector_store import MemoryStore
from .Memory.retriever import MemoryRetriever
from .Memory.extractor import MemoryExtractor
from .Memory.consolidator import MemoryConsolidator, SessionClosingCache

from managers.mongodb_manager import MongoDBManager

from shared.logging_config import get_logger

logger = get_logger(__name__)


class TeachingAssistant:
    """
    Enhanced TeachingAssistant with memory management, skills, and event processing.
    Maintains backward compatibility with existing API methods.
    """

    def __init__(self):
        # MongoDB session manager (existing)
        mongo = MongoDBManager()
        self.session_manager = SessionManager(mongo)
        
        # Event processing components
        self.queue_manager = EventQueueManager()
        self.context_manager = ContextManager()
        self.event_processor = EventProcessor(self.context_manager, None)  # Skills added later
        
        # Injection manager (uses MongoDB queue)
        self.injection_manager = InjectionManager()
        
        # Skills system
        self.skills_manager = SkillsManager()
        
        # Memory system
        self.memory_stores: Dict[str, MemoryStore] = {}
        self.memory_extractor = MemoryExtractor()
        self.memory_consolidators: Dict[str, MemoryConsolidator] = {}
        self.memory_retrievers: Dict[str, MemoryRetriever] = {}
        self.closing_caches: Dict[str, SessionClosingCache] = {}
        
        # Greeting handler (memory-aware from v3)
        self.greeting_handler = GreetingHandler()
        
        # Event processing loop
        self.running = False
        
        # Update event processor with skills manager
        self.event_processor.skills_manager = self.skills_manager
        
        logger.info("[TEACHING_ASSISTANT] Initialized with MongoDB-backed session manager, memory system, and skills")

    def start_session(self, user_id: str) -> dict:
        """Start a new session, returns greeting prompt and session info"""
        session = self.session_manager.create_session(user_id)
        greeting = self.greeting_handler.get_greeting(user_id)
        return {
            "session_id": session["session_id"],
            "prompt": greeting,
            "session_info": self.session_manager.get_session_info(session["session_id"])
        }

    def end_session(self, session_id: str) -> dict:
        """End session, returns closing prompt with stats"""
        session_summary = self.session_manager.end_session(session_id)
        if not session_summary:
            return {
                "prompt": "",
                "session_info": {"session_active": False}
            }

        closing = self.greeting_handler.get_closing(
            duration_minutes=session_summary.get("duration_minutes", 0),
            questions_answered=session_summary.get("questions_answered", 0)
        )
        return {
            "prompt": closing,
            "session_info": session_summary
        }

    def record_question_answered(
        self,
        session_id: str,
        question_id: str,
        is_correct: bool
    ) -> None:
        """Record a question answer"""
        self.session_manager.record_question_answered(session_id, is_correct)

    def record_conversation_turn(self, session_id: str) -> None:
        """Record a conversation turn"""
        self.session_manager.record_conversation_turn(session_id)

    def check_inactivity(self, session_id: str) -> Optional[str]:
        """Check inactivity and return prompt if needed"""
        if self.session_manager.check_inactivity(session_id):
            prompt = self.greeting_handler.get_inactivity_prompt()
            self.session_manager.push_instruction(session_id, prompt)
            return prompt
        return None

    def get_session_info(self, session_id: str) -> dict:
        """Get current session info"""
        return self.session_manager.get_session_info(session_id)

    def get_active_session(self, user_id: str) -> Optional[dict]:
        """Get active session for user"""
        return self.session_manager.get_active_session(user_id)

    def push_instruction(self, session_id: str, instruction: str) -> str:
        """Push an instruction to be delivered via SSE"""
        return self.session_manager.push_instruction(session_id, instruction)

    # ============================================================================
    # New Methods for Memory, Skills, and Event Processing
    # ============================================================================

    def _get_or_create_memory_store(self, user_id: str) -> MemoryStore:
        """Get or create MemoryStore for user"""
        if user_id not in self.memory_stores:
            logger.info(f"[TEACHING_ASSISTANT] Creating MemoryStore for user: {user_id}")
            self.memory_stores[user_id] = MemoryStore(user_id=user_id)
        return self.memory_stores[user_id]

    async def start(self, user_id: str, session_id: str) -> Optional[str]:
        """
        Start session with memory and context initialization.
        Called after session is created in MongoDB.
        """
        # Get session to get start_time
        session = self.session_manager.get_session_by_id(session_id)
        if not session:
            return None
        
        # Parse start_time from MongoDB datetime
        start_time = session["started_at"]
        if hasattr(start_time, 'timestamp'):
            start_time = start_time.timestamp()
        elif isinstance(start_time, str):
            from datetime import datetime
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00')).timestamp()
        else:
            start_time = time.time()
        
        # Create context
        self.context_manager.create_context(session_id, user_id, start_time)
        
        # Initialize memory components
        memory_store = self._get_or_create_memory_store(user_id)
        
        if user_id not in self.memory_consolidators:
            self.memory_consolidators[user_id] = MemoryConsolidator(memory_store, self.memory_extractor)
        
        memory_retriever = MemoryRetriever(memory_store)
        self.memory_retrievers[session_id] = memory_retriever
        
        closing_cache = SessionClosingCache(session_id, user_id)
        self.closing_caches[session_id] = closing_cache
        

        
        # Get greeting (memory-aware)
        greeting = self.greeting_handler.start_session(user_id, session_id)

        # Also record greeting into conversation context so it appears in saved history
        context = self.context_manager.get_context(session_id)
        if context and greeting:
            # Use session start_time as an approximate timestamp for the greeting
            ts = context.start_time or time.time()
            context.add_turn(speaker="adam", text=greeting, timestamp=ts)

        # Send greeting via instruction queue
        if greeting:
            await self.injection_manager.send_to_adam(greeting, session_id, user_id)

        return greeting

    async def ongoing(self):
        """Main event processing loop"""
        while self.running:
            # Dequeue batch of events
            events = self.queue_manager.dequeue_batch(max_batch_size=5)
            
            if events:
                for event in events:
                    # Handle session lifecycle events
                    if event.type == 'session_start':
                        # Session initialization and greeting are handled in the API layer
                        # via `ta.start(...)` to avoid double greetings.
                        continue
                    elif event.type == 'session_end':
                        await self._handle_session_end(event)
                        continue
                    
                    # Update context from event
                    self.context_manager.update_from_event(event)
                    
                    # Process text events for memory
                    if event.type == 'text':
                        speaker = event.data.get('speaker')
                        text = event.data.get('text', '')
                        timestamp = event.timestamp
                        
                        context = self.context_manager.get_context(event.session_id)
                        closing_cache = self.closing_caches.get(event.session_id)
                        memory_retriever = self.memory_retrievers.get(event.session_id)
                        
                        if speaker == 'user' and context and text:
                            user_text = text
                            adam_text = context.last_adam_text or ""
                            
                            # Trigger TA-light retrieval (async) but debounce to avoid
                            # running on every tiny turn in very quick succession.
                            if memory_retriever:
                                # simple debounce: skip if last retrieval was < 5s ago
                                last_rt = context.last_retrieval_time or 0
                                if (timestamp - last_rt) >= 5.0:
                                    context.last_retrieval_time = timestamp
                                    asyncio.create_task(self._trigger_memory_retrieval_async(
                                        memory_retriever=memory_retriever,
                                        session_id=event.session_id,
                                        user_id=event.user_id,
                                        user_text=user_text,
                                        timestamp=timestamp,
                                        adam_text=adam_text
                                    ))
                            
                            # Trigger memory extraction (async)
                            if closing_cache:
                                asyncio.create_task(self._extract_memories_async(
                                    closing_cache=closing_cache,
                                    user_text=user_text,
                                    adam_text=adam_text,
                                    topic=event.data.get('topic', 'general'),
                                    session_id=event.session_id
                                ))
                    
                    # Process event through skills
                    injections = self.event_processor.process_event(event)
                    
                    # Send injections, but avoid queueing exact duplicates back-to-back
                    if injections:
                        context = self.context_manager.get_context(event.session_id)
                        last_injected: Optional[str] = getattr(context, "_last_injection", None) if context else None
                        for injection in injections:
                            if not injection:
                                continue
                            if last_injected and injection.strip() == last_injected.strip():
                                continue
                            await self.injection_manager.send_to_adam(
                                injection,
                                event.session_id,
                                event.user_id
                            )
                            if context:
                                setattr(context, "_last_injection", injection.strip())
            else:
                # No events - execute skills on all active sessions
                active_sessions = self.session_manager.list_active_sessions()
                for session in active_sessions:
                    session_id = session["session_id"]
                    context = self.context_manager.get_context(session_id)
                    if context:
                        injections = self.skills_manager.execute_skills(context)
                        for injection in injections:
                            if injection:
                                await self.injection_manager.send_to_adam(
                                    injection,
                                    session_id,
                                    session["user_id"]
                                )
            
            if not events:
                await asyncio.sleep(0.01)  # Small delay when no events

    async def end(self, user_id: str, session_id: str) -> Optional[str]:
        """End session with memory consolidation"""
        # Get context before clearing
        context = self.context_manager.get_context(session_id)
        
        if context:
            # Flush any remaining turn
            context.flush_current_turn()
            
            # Save conversation
            await self._save_conversation_async(user_id, session_id, context)
        
        # Consolidate memories
        closing_cache = self.closing_caches.get(session_id)
        if closing_cache:
            consolidator = self.memory_consolidators.get(user_id)
            if consolidator:
                consolidator.consolidate_session(user_id, session_id, closing_cache)
            del self.closing_caches[session_id]
        
        # Clean up memory retriever
        memory_retriever = self.memory_retrievers.get(session_id)
        if memory_retriever:
            memory_retriever.clear_session(session_id)
            del self.memory_retrievers[session_id]
        
        # Clear context
        self.context_manager.clear_context(session_id)
        
        # Get closing message (memory-aware)
        closing = self.greeting_handler.end_session(user_id, session_id)
        
        # Send closing via instruction queue
        if closing:
            await self.injection_manager.send_to_adam(closing, session_id, user_id)
        
        return closing

    async def _trigger_memory_retrieval_async(self, memory_retriever: MemoryRetriever, session_id: str, 
                                               user_id: str, user_text: str, timestamp: float, adam_text: str):
        """Trigger memory retrieval (TA-light and TA-deep) asynchronously and inject memories after completion"""
        try:
            # Run memory retrieval in executor to avoid blocking (Pinecone queries can be slow)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                memory_retriever.on_user_turn,
                session_id,
                user_id,
                user_text,
                timestamp,
                adam_text
            )
            logger.info(f"[TEACHING_ASSISTANT] Memory retrieval completed for session: {session_id}")
            
            # After retrieval completes, get injection and send it
            injection_text = memory_retriever.get_memory_injection(session_id)
            if injection_text:
                logger.info(f"[TEACHING_ASSISTANT] Memory injection ready for session: {session_id}")
                await self.injection_manager.send_to_adam(
                    injection_text,
                    session_id,
                    user_id
                )
        except Exception as e:
            logger.error(f"[TEACHING_ASSISTANT] Error in async memory retrieval: {e}", exc_info=True)

    async def _extract_memories_async(self, closing_cache, user_text: str, adam_text: str, topic: str, session_id: str):
        """Extract memories asynchronously without blocking the event loop"""
        try:
            # Get user_id from closing_cache
            user_id = closing_cache.user_id
            
            # Get user-specific memory store
            memory_store = self._get_or_create_memory_store(user_id)
            
            # Run memory extraction in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                closing_cache.update_after_exchange,
                user_text,
                adam_text,
                topic,
                self.memory_extractor,
                memory_store
            )
            logger.info(f"[TEACHING_ASSISTANT] Memory extraction completed for session: {session_id}")
        except Exception as e:
            logger.error(f"[TEACHING_ASSISTANT] Error in async memory extraction: {e}", exc_info=True)

    async def _save_conversation_async(self, user_id: str, session_id: str, context):
        """Save conversation to file (non-blocking via thread executor)"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._save_conversation_sync, user_id, session_id, context)
    
    def _save_conversation_sync(self, user_id: str, session_id: str, context):
        """Synchronous file save (runs in thread executor)"""
        import os
        import json
        from datetime import datetime
        
        try:
            data_dir = f"services/TeachingAssistant/Memory/data/{user_id}/conversations"
            os.makedirs(data_dir, exist_ok=True)
            
            file_path = f"{data_dir}/{session_id}.json"
            conversation_data = {
                "session_id": session_id,
                "user_id": user_id,
                "start_time": datetime.fromtimestamp(context.start_time).isoformat(),
                "end_time": datetime.now().isoformat(),
                "turn_count": context.turn_count,
                "turns": context.conversation_turns
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"[TEACHING_ASSISTANT] Saved conversation to {file_path} ({len(context.conversation_turns)} turns)")
        except Exception as e:
            logger.error(f"[TEACHING_ASSISTANT] Error saving conversation: {e}", exc_info=True)



    async def _handle_session_end(self, event):
        """Handle session end event"""
        session = self.session_manager.get_session_by_id(event.session_id)
        if session:
            await self.end(session["user_id"], event.session_id)
