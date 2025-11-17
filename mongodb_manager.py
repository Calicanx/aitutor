"""
MongoDB Connection Manager for AI Tutor System
Centralized MongoDB connection and collection access
"""

from pymongo import MongoClient
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)

class MongoDBManager:
    """Singleton MongoDB connection manager"""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._connect()
    
    def _connect(self):
        """Establish MongoDB connection"""
        try:
            # Get connection string from environment or use from test file
            mongo_uri = os.getenv(
                'MONGODB_URI',
                'mongodb+srv://imdadshozab_db_user:iuCgDzZJ1n9sKmo7@aitutor.ut0qoxu.mongodb.net/?appName=AiTutor'
            )
            
            self._client = MongoClient(mongo_uri)
            self._db = self._client['aitutor']
            
            # Test connection
            self._client.admin.command('ping')
            logger.info(f"[MONGODB] Connected to database: aitutor")
            
        except Exception as e:
            logger.error(f"[MONGODB] Connection failed: {e}")
            raise
    
    @property
    def db(self):
        """Get database instance"""
        return self._db
    
    @property
    def users(self):
        """Get users collection"""
        return self._db['users']
    
    @property
    def perseus_questions(self):
        """Get perseus_questions collection"""
        return self._db['perseus_questions']
    
    @property
    def dash_questions(self):
        """Get dash_questions collection"""
        return self._db['dash_questions']
    
    @property
    def skills(self):
        """Get skills collection"""
        return self._db['skills']
    
    def test_connection(self):
        """Test if MongoDB connection is working"""
        try:
            self._client.admin.command('ping')
            collections = self._db.list_collection_names()
            logger.info(f"[MONGODB] Connection OK. Collections: {collections}")
            return True
        except Exception as e:
            logger.error(f"[MONGODB] Connection test failed: {e}")
            return False
    
    def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            logger.info("[MONGODB] Connection closed")

# Create global instance
mongo_db = MongoDBManager()

