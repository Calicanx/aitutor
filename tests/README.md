# AI Tutor - Test Suite

## Overview
This directory contains the test suite for the AI Tutor application.

## Test Structure

```
tests/
├── test_jwt_config.py          # JWT configuration tests
├── test_retry_utils.py         # Retry utilities tests
├── unit/                       # Unit tests (to be added)
├── integration/                # Integration tests (to be added)
└── e2e/                        # End-to-end tests (to be added)
```

## Running Tests

### Install Test Dependencies
```bash
pip install -r requirements-test.txt
```

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_jwt_config.py
```

### Run with Coverage
```bash
pytest --cov=shared --cov=services --cov=managers
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Only Unit Tests
```bash
pytest -m unit
```

### Run Only Integration Tests
```bash
pytest -m integration
```

## Test Markers

Tests can be marked with the following markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow running tests
- `@pytest.mark.security` - Security-related tests
- `@pytest.mark.api` - API endpoint tests

## Writing Tests

### Unit Test Example
```python
import pytest
from shared.jwt_config import validate_jwt_secret

class TestJWTValidation:
    def test_strong_secret_passes(self):
        """Test that strong secrets pass validation"""
        secret = "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"
        assert validate_jwt_secret(secret) is True
```

### Integration Test Example
```python
import pytest
from fastapi.testclient import TestClient
from services.AuthService.auth_api import app

@pytest.mark.integration
class TestAuthAPI:
    def test_health_endpoint(self):
        """Test health check endpoint"""
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
```

## Coverage Goals

- **Minimum Coverage:** 50%
- **Target Coverage:** 80%
- **Critical Modules:** 90%+ (JWT, Auth, DASH)

## Current Coverage

Run `pytest --cov` to see current coverage report.

## CI/CD Integration

Tests are configured to run automatically on:
- Pull requests
- Commits to main branch
- Pre-deployment checks

## Test Data

Test data and fixtures should be placed in:
- `tests/fixtures/` - Shared test fixtures
- `tests/data/` - Test data files

## Mocking

Use `pytest-mock` for mocking external dependencies:

```python
def test_with_mock(mocker):
    mock_api = mocker.patch('services.api.external_call')
    mock_api.return_value = {"status": "ok"}
    # Test code here
```

## Best Practices

1. **Test Naming:** Use descriptive names that explain what is being tested
2. **Arrange-Act-Assert:** Structure tests clearly
3. **One Assertion:** Focus each test on one behavior
4. **Independent Tests:** Tests should not depend on each other
5. **Fast Tests:** Keep unit tests fast (< 100ms)
6. **Mock External:** Mock external APIs and databases in unit tests

## Troubleshooting

### Import Errors
Make sure you're running tests from the project root:
```bash
cd /path/to/ai_tutor_run_time_optimisation
pytest
```

### Coverage Not Working
Install coverage extras:
```bash
pip install coverage[toml]
```

### Slow Tests
Skip slow tests during development:
```bash
pytest -m "not slow"
```

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure tests pass locally
3. Maintain or improve coverage
4. Add integration tests for APIs
5. Document complex test scenarios

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
