# Testing Documentation - PartsHub Backend

This document outlines the standardized testing approach for the PartsHub backend, including database isolation, fixtures, and authentication patterns.

## Testing Philosophy

PartsHub follows **Test-Driven Development (TDD)** with strict **Testing Isolation** principles:

- **Tests MUST NEVER use live production databases**
- **Each test gets a fresh, isolated database**
- **Tests use different ports from production** (test: 8005, prod: 8000)
- **Fixtures provide consistent, reusable test data**
- **Authentication is handled through standardized fixtures**

## Test Environment Isolation

Tests are configured to run with complete isolation from production:

- **Database**: In-memory SQLite (`sqlite:///:memory:`)
- **Port**: 8005 (production uses 8000)
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
- **Port Isolation**: Tests run on port 8005, production on 8000
- **Clean State**: Each test gets fresh database with no data persistence
- **Admin User**: Default admin creation disabled during tests

## Authentication Fixtures

### Standard Authentication Pattern

All tests requiring authentication should use the standardized fixtures:

```python
@pytest.fixture
def auth_headers(client):
    """Provides authentication headers for API requests"""
    # Create test user and get JWT token
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }

    # Register user
    client.post("/api/v1/auth/register", json=user_data)

    # Login and get token
    login_response = client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "testpass123"
    })

    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client):
    """Provides admin authentication headers"""
    # Similar pattern but creates admin user
    # Implementation depends on admin creation logic
    pass
```

### Database Session Isolation

Tests use dependency injection to ensure proper database session handling:

```python
@pytest.fixture
def test_db():
    """Create test database session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()

def override_get_db(test_db):
    """Override FastAPI database dependency"""
    return test_db
```

## Test Data Fixtures

### Component Test Data

Standard fixtures for electronic components testing:

```python
@pytest.fixture
def sample_category(client, auth_headers):
    """Create test category"""
    category_data = {
        "name": "Test Category",
        "description": "For testing purposes"
    }
    response = client.post("/api/v1/categories",
                         json=category_data,
                         headers=auth_headers)
    return response.json()

@pytest.fixture
def sample_component(client, auth_headers, sample_category):
    """Create test electronic component"""
    component_data = {
        "name": "Test Resistor",
        "part_number": "R001",
        "manufacturer": "Test Mfg",
        "category_id": sample_category["id"],
        "component_type": "resistor",
        "value": "10k",
        "package": "0603",
        "specifications": {
            "resistance": "10kΩ",
            "tolerance": "±1%"
        }
    }
    response = client.post("/api/v1/components",
                         json=component_data,
                         headers=auth_headers)
    return response.json()
```

## Test Patterns

### Contract Testing Pattern

API endpoints should follow this contract testing pattern:

```python
def test_create_component_contract(client, auth_headers):
    """Test component creation follows OpenAPI contract"""

    # Valid request
    valid_data = {
        "name": "Test Component",
        "part_number": "TC001",
        "manufacturer": "TestCorp"
    }

    response = client.post("/api/v1/components",
                         json=valid_data,
                         headers=auth_headers)

    # Contract assertions
    assert response.status_code == 201
    assert "id" in response.json()
    assert response.json()["name"] == valid_data["name"]

    # Invalid request
    invalid_data = {"name": ""}  # Missing required fields

    response = client.post("/api/v1/components",
                         json=invalid_data,
                         headers=auth_headers)

    assert response.status_code == 422
    assert "detail" in response.json()
```

### Integration Test Pattern

End-to-end workflow testing:

```python
def test_component_lifecycle_integration(client, auth_headers):
    """Test complete component management workflow"""

    # 1. Create category
    category = create_test_category(client, auth_headers)

    # 2. Create component
    component = create_test_component(client, auth_headers, category["id"])

    # 3. Update component
    updated_data = {"quantity_on_hand": 50}
    update_response = client.put(f"/api/v1/components/{component['id']}",
                               json=updated_data,
                               headers=auth_headers)
    assert update_response.status_code == 200

    # 4. Search component
    search_response = client.get(f"/api/v1/components?search={component['name']}")
    assert len(search_response.json()) > 0

    # 5. Delete component
    delete_response = client.delete(f"/api/v1/components/{component['id']}",
                                  headers=auth_headers)
    assert delete_response.status_code == 200
```

## Best Practices

### Test Organization

- **Unit Tests** (`tests/unit/`): Model logic, business rules, utilities
- **Contract Tests** (`tests/contract/`): API endpoint behavior per OpenAPI spec
- **Integration Tests** (`tests/integration/`): End-to-end workflows

### Database Testing Rules

1. **Never touch production data**: Always use in-memory SQLite
2. **Fresh state per test**: Each test gets clean database
3. **Predictable data**: Use fixtures for consistent test data
4. **Transaction rollback**: Tests should not persist changes

### Authentication Testing

1. **Use standard fixtures**: `auth_headers` and `admin_headers`
2. **Test both authenticated and unauthenticated flows**
3. **Verify proper authorization levels**
4. **Test token expiration and refresh**

### Performance Testing

1. **Reasonable test execution time**: Aim for <2 seconds per test
2. **Database query optimization**: Monitor N+1 queries in tests
3. **Parallel test execution**: Tests must be independent
4. **Resource cleanup**: Prevent memory leaks in test suite

## Troubleshooting

### Common Issues

**Authentication Dependency Injection**
- *Problem*: Auth tests fail due to database session mismatch
- *Solution*: Ensure test client and auth system share same database session
- *Code*: Use `app.dependency_overrides` in test setup

**Test Database Persistence**
- *Problem*: Test data persists between tests
- *Solution*: Verify `sqlite:///:memory:` usage and session cleanup
- *Code*: Check `TESTING=1` environment variable

**Port Conflicts**
- *Problem*: Tests fail with "address already in use"
- *Solution*: Ensure tests use port 8005, production uses 8000
- *Code*: Verify `PORT=8005` in test environment

**Fixture Dependencies**
- *Problem*: Test fixtures load in wrong order
- *Solution*: Explicit fixture dependencies in function parameters
- *Code*: `def test_func(auth_headers, sample_component):`

### Debugging Test Failures

1. **Isolate the test**: Run single test with `python run_tests.py tests/unit/test_specific.py`
2. **Check test output**: Use `-v` flag for verbose output
3. **Verify environment**: Ensure `TESTING=1` and correct database URL
4. **Database state**: Add debug prints to verify test data creation
5. **Authentication flow**: Verify JWT token creation and validation

## Current Issues

The remaining contract test failures are due to a FastAPI dependency injection issue where the authentication system doesn't share the same database session as the test fixtures. This is a complex architectural challenge that requires significant changes to resolve fully.

## Environment Variables

| Variable | Production | Tests |
|----------|------------|-------|
| `DATABASE_URL` | `sqlite:///./data/partshub.db` | `sqlite:///:memory:` |
| `PORT` | `8000` | `8005` |
| `TESTING` | Not set | `1` |
| `SECRET_KEY` | Production secret | `test-secret-key-not-for-production` |