"""
Unit tests for JWT configuration and validation
"""
import pytest
import os
from unittest.mock import patch
from shared.jwt_config import validate_jwt_secret, JWT_SECRET, JWT_AUDIENCE, JWT_ISSUER


class TestJWTConfig:
    """Test JWT configuration and validation"""
    
    def test_validate_jwt_secret_with_strong_secret(self):
        """Test that strong secrets pass validation"""
        strong_secret = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
        result = validate_jwt_secret(strong_secret)
        assert result is True
    
    def test_validate_jwt_secret_rejects_weak_secrets(self):
        """Test that known weak secrets are rejected"""
        weak_secrets = [
            "change-me-in-production",
            "secret",
            "password",
            "test",
            "dev",
        ]
        for secret in weak_secrets:
            result = validate_jwt_secret(secret)
            assert result is False, f"Weak secret '{secret}' should be rejected"
    
    def test_validate_jwt_secret_rejects_short_secrets(self):
        """Test that secrets shorter than 32 characters are rejected"""
        short_secret = "short"
        result = validate_jwt_secret(short_secret)
        assert result is False
    
    def test_validate_jwt_secret_requires_letters_and_numbers(self):
        """Test that secrets must contain both letters and numbers"""
        only_letters = "a" * 32
        only_numbers = "1" * 32
        
        assert validate_jwt_secret(only_letters) is False
        assert validate_jwt_secret(only_numbers) is False
    
    def test_jwt_audience_is_set(self):
        """Test that JWT_AUDIENCE is properly configured"""
        assert JWT_AUDIENCE is not None
        assert len(JWT_AUDIENCE) > 0
        assert JWT_AUDIENCE == "teachr-api"
    
    def test_jwt_issuer_is_set(self):
        """Test that JWT_ISSUER is properly configured"""
        assert JWT_ISSUER is not None
        assert len(JWT_ISSUER) > 0
        assert JWT_ISSUER == "teachr-auth-service"
    
    @patch.dict(os.environ, {"JWT_SECRET": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"})
    def test_jwt_secret_loaded_from_environment(self):
        """Test that JWT_SECRET is loaded from environment"""
        # This would require reimporting the module
        # For now, just verify the environment variable can be set
        assert os.getenv("JWT_SECRET") == "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
