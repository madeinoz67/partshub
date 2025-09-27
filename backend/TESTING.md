# Testing Guide

## Test Environment Isolation

Tests are configured to run with complete isolation from production:

- **Database**: In-memory SQLite (`sqlite:///:memory:`)
- **Port**: 8001 (production uses 8000)
- **Environment**: `TESTING=1` flag set

## Running Tests

### Option 1: Isolated Test Runner (Recommended)
```bash
# Run all tests with isolation
python run_tests.py

# Run specific test file
python run_tests.py tests/unit/test_storage_model.py

# Run with pytest options
python run_tests.py -v --tb=short
```

### Option 2: Direct pytest (Manual Environment)
```bash
# Set environment variables manually
export TESTING=1
export DATABASE_URL="sqlite:///:memory:"
export PORT=8001

# Run tests
uv run pytest
```

## Test Types

### Unit Tests (`tests/unit/`)
- Model functionality and business logic
- Database relationships and validation
- **Status**: ✅ 28/28 passing

### Contract Tests (`tests/contract/`)
- API endpoint behavior according to OpenAPI spec
- Authentication and authorization
- **Status**: 🟡 135/185 passing (73% success rate)

### Integration Tests (`tests/integration/`)
- End-to-end workflows
- **Status**: 🚧 Pending implementation

## Test Database Safety

- **Production Safety**: Tests use in-memory database, never touch production data
- **Port Isolation**: Tests run on port 8001, production on 8000
- **Clean State**: Each test gets fresh database with no data persistence
- **Admin User**: Default admin creation disabled during tests

## Current Issues

The remaining contract test failures are due to a FastAPI dependency injection issue where the authentication system doesn't share the same database session as the test fixtures. This is a complex architectural challenge that requires significant changes to resolve fully.

## Environment Variables

| Variable | Production | Tests |
|----------|------------|-------|
| `DATABASE_URL` | `sqlite:///./data/partshub.db` | `sqlite:///:memory:` |
| `PORT` | `8000` | `8001` |
| `TESTING` | Not set | `1` |
| `SECRET_KEY` | Production secret | `test-secret-key-not-for-production` |