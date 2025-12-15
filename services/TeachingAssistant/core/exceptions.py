"""
Custom exceptions for TeachingAssistant service.
"""

class TAError(Exception):
    """Base exception for TeachingAssistant service"""
    pass

class DatabaseConnectionError(TAError):
    """Raised when database connection fails"""
    pass

class LLMGenerationError(TAError):
    """Raised when LLM generation fails"""
    pass

class VectorStoreError(TAError):
    """Raised when vector store operations fail"""
    pass

class SessionError(TAError):
    """Raised when session operations fail"""
    pass
