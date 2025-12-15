"""
Context Manager for TeachingAssistant
Manages session context with MongoDB persistence and in-memory caching.
"""

from typing import Optional
import time
import logging

from .context import SessionContext, Event
from managers.mongodb_manager import MongoDBManager

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages session context with MongoDB persistence.
    Uses in-memory cache for performance, syncs to MongoDB periodically.
    """
    
    def __init__(self):
        mongo = MongoDBManager()
        self.db = mongo.db
        self.contexts = self.db.session_contexts
        self._in_memory_cache = {}  # Cache for performance
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Create indexes for efficient queries"""
        try:
            self.contexts.create_index("session_id", unique=True)
            self.contexts.create_index("user_id")
            logger.info("[CONTEXT_MANAGER] Indexes ensured on session_contexts collection")
        except Exception as e:
            logger.error(f"[CONTEXT_MANAGER] Failed to create indexes: {e}")
    
    def create_context(self, session_id: str, user_id: str, start_time: float):
        """Create new context in MongoDB and cache"""
        context = SessionContext(
            session_id=session_id,
            user_id=user_id,
            start_time=start_time
        )
        # Save to MongoDB
        self.contexts.update_one(
            {"session_id": session_id},
            {"$set": context.to_mongodb_dict()},
            upsert=True
        )
        # Cache in memory
        self._in_memory_cache[session_id] = context
        logger.info(f"[CONTEXT_MANAGER] Created context for session {session_id}")
    
    def get_context(self, session_id: str) -> Optional[SessionContext]:
        """Get context from cache or MongoDB"""
        # Check cache first
        if session_id in self._in_memory_cache:
            return self._in_memory_cache[session_id]
        
        # Load from MongoDB
        data = self.contexts.find_one({"session_id": session_id})
        if data:
            context = SessionContext.from_mongodb_dict(data)
            self._in_memory_cache[session_id] = context
            return context
        return None
    
    def update_from_event(self, event: Event):
        """Update context from event and sync to MongoDB"""
        context = self.get_context(event.session_id)
        if not context:
            return
        
        # Update context based on event type
        if event.type == 'text':
            speaker = event.data.get('speaker')
            text = event.data.get('text', '')
            timestamp = event.timestamp
            
            context.add_turn(speaker, text, timestamp)
            context.last_activity_time = timestamp
            
            if speaker == 'user':
                context.last_user_text = text
                context.last_user_turn_time = timestamp
            elif speaker == 'tutor' or speaker == 'adam':
                context.last_adam_text = text
                context.last_adam_turn_time = timestamp
        
        # Mark dirty instead of syncing immediately
        context.is_dirty = True
    
    def _sync_to_mongodb(self, context: SessionContext):
        """Sync context to MongoDB"""
        try:
            self.contexts.update_one(
                {"session_id": context.session_id},
                {"$set": context.to_mongodb_dict()},
                upsert=True
            )
        except Exception as e:
            logger.error(f"[CONTEXT_MANAGER] Error syncing context to MongoDB: {e}")
            
    def sync_dirty_contexts(self):
        """Sync all dirty contexts to MongoDB"""
        dirty_count = 0
        for session_id, context in list(self._in_memory_cache.items()):
            if context.is_dirty:
                self._sync_to_mongodb(context)
                context.is_dirty = False
                dirty_count += 1
        
        if dirty_count > 0:
            logger.debug(f"[CONTEXT_MANAGER] Synced {dirty_count} dirty contexts to MongoDB")
    
    def clear_context(self, session_id: str):
        """Clear context from cache and MongoDB"""
        if session_id in self._in_memory_cache:
            del self._in_memory_cache[session_id]
        try:
            self.contexts.delete_one({"session_id": session_id})
            logger.info(f"[CONTEXT_MANAGER] Cleared context for session {session_id}")
        except Exception as e:
            logger.error(f"[CONTEXT_MANAGER] Error clearing context: {e}")
