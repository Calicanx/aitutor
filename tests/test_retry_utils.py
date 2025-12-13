"""
Unit tests for retry utilities
"""
import pytest
import time
from shared.retry_utils import (
    retry_with_backoff,
    safe_execute,
    RetryableError,
    NonRetryableError,
    ErrorHandler
)


class TestRetryWithBackoff:
    """Test retry decorator functionality"""
    
    def test_successful_execution_no_retry(self):
        """Test that successful functions don't retry"""
        call_count = 0
        
        @retry_with_backoff(retries=3)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_function()
        assert result == "success"
        assert call_count == 1
    
    def test_retries_on_exception(self):
        """Test that function retries on exception"""
        call_count = 0
        
        @retry_with_backoff(retries=3, backoff_factor=0.1)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"
        
        result = failing_function()
        assert result == "success"
        assert call_count == 3
    
    def test_raises_after_max_retries(self):
        """Test that exception is raised after max retries"""
        call_count = 0
        
        @retry_with_backoff(retries=3, backoff_factor=0.1)
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Permanent error")
        
        with pytest.raises(ValueError):
            always_failing_function()
        
        assert call_count == 3
    
    def test_specific_exception_types(self):
        """Test retry only on specific exceptions"""
        call_count = 0
        
        @retry_with_backoff(retries=3, exceptions=(RetryableError,), backoff_factor=0.1)
        def selective_retry():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RetryableError("Should retry")
            return "success"
        
        result = selective_retry()
        assert result == "success"
        assert call_count == 2
    
    def test_non_retryable_error_fails_immediately(self):
        """Test that non-retryable errors fail immediately"""
        call_count = 0
        
        @retry_with_backoff(retries=3, exceptions=(RetryableError,), backoff_factor=0.1)
        def non_retryable_error():
            nonlocal call_count
            call_count += 1
            raise NonRetryableError("Should not retry")
        
        with pytest.raises(NonRetryableError):
            non_retryable_error()
        
        assert call_count == 1


class TestSafeExecute:
    """Test safe_execute utility"""
    
    def test_returns_result_on_success(self):
        """Test that result is returned on success"""
        result = safe_execute(lambda: "success")
        assert result == "success"
    
    def test_returns_default_on_error(self):
        """Test that default is returned on error"""
        result = safe_execute(
            lambda: 1 / 0,
            default="error",
            log_errors=False
        )
        assert result == "error"
    
    def test_returns_none_by_default(self):
        """Test that None is returned by default on error"""
        result = safe_execute(lambda: 1 / 0, log_errors=False)
        assert result is None


class TestErrorHandler:
    """Test ErrorHandler context manager"""
    
    def test_suppresses_errors_by_default(self):
        """Test that errors are suppressed by default"""
        with ErrorHandler("test operation") as handler:
            raise ValueError("Test error")
        
        assert handler.error is not None
        assert isinstance(handler.error, ValueError)
    
    def test_raises_errors_when_configured(self):
        """Test that errors can be re-raised"""
        with pytest.raises(ValueError):
            with ErrorHandler("test operation", raise_on_error=True):
                raise ValueError("Test error")
    
    def test_no_error_on_success(self):
        """Test that no error is recorded on success"""
        with ErrorHandler("test operation") as handler:
            x = 1 + 1
        
        assert handler.error is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
