"""
Pytest configuration and shared fixtures
"""

import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.src.auth.jwt_auth import create_access_token
from backend.src.database import get_db
from backend.src.main import app
from backend.src.models import APIToken, User

# Set testing environment variables to ensure complete isolation
os.environ["TESTING"] = "1"
os.environ[
    "DATABASE_URL"
] = "sqlite:///:memory:"  # Use in-memory database for complete isolation
os.environ["PORT"] = "8005"  # Use different port for tests (production uses 8000)

# Test database URL - in-memory database for complete isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with proper configuration
test_engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False,  # Set to True for debugging SQL issues
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def apply_migrations():
    """Apply all Alembic migrations to the test database"""
    # Set environment variable for test database
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL

    # Load Alembic configuration
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

    # Run migrations
    command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    """
    Set up fresh in-memory test database for each test with proper model loading
    """
    # Import the Base from the correct database module
    import backend.src.database.search as search_module
    from backend.src.database import Base
    from backend.src.database.search import ComponentSearchService

    # Import all models to ensure they are registered with SQLAlchemy
    # This is critical for table creation to work properly

    # Reset global FTS service singleton to ensure test isolation
    search_module._component_search_service = None

    # Enable SQLite-specific features for test database
    with test_engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))
        conn.execute(text("PRAGMA journal_mode=MEMORY"))  # Use memory mode for tests
        conn.commit()

    # Create all tables with proper metadata
    Base.metadata.create_all(bind=test_engine)

    # Initialize FTS table and triggers BEFORE any tests run
    # This ensures triggers are in place when components are created
    session = TestingSessionLocal()
    try:
        search_service = ComponentSearchService()
        search_service._ensure_fts_table(session)
        session.commit()
    except Exception as e:
        print(f"Warning: Failed to initialize FTS table: {e}")
        session.rollback()
    finally:
        session.close()

    yield

    # Clean up: Drop all tables after test for complete isolation
    Base.metadata.drop_all(bind=test_engine)

    # Reset global FTS service singleton after test
    search_module._component_search_service = None


@pytest.fixture(scope="function")
def db_session():
    """
    Create a database session for each test with proper transaction management
    """
    import backend.src.database.search as search_module
    from sqlalchemy import text

    # Reset FTS singleton before each test for isolation
    search_module._component_search_service = None

    session = TestingSessionLocal()
    try:
        # Start a transaction that will be rolled back after the test
        session.begin()
        yield session
    except Exception:
        # Rollback on any exception
        session.rollback()
        raise
    finally:
        # Clean up FTS table explicitly (virtual tables don't always respect rollback)
        try:
            session.execute(text("DELETE FROM components_fts"))
            session.commit()
        except Exception:
            # Table might not exist, that's ok
            pass

        # Always close the session to release resources
        session.close()

        # Reset FTS singleton after each test
        search_module._component_search_service = None


# Remove global_test_users fixture to avoid duplicate user creation
# Individual test fixtures will create users as needed


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with database session override
    """

    def override_get_db():
        """Override database dependency with the test session"""
        try:
            yield db_session
        finally:
            pass  # Session cleanup is handled by the db_session fixture

    # Override the database dependency for the test
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # Always clean up dependency overrides after test
        app.dependency_overrides.clear()


@pytest.fixture
def sample_component_data():
    """
    Sample component data for tests
    Note: quantity_on_hand and minimum_stock are NOT included here as they require
    ComponentLocation records. Tests should add stock using the stock API endpoints.
    """
    return {
        "name": "Resistor 10kΩ 1% 0805",
        "part_number": "RC0805FR-0710KL",
        "manufacturer": "Yageo",
        "component_type": "resistor",
        "value": "10kΩ",
        "package": "0805",
        "specifications": {
            "resistance": "10kΩ",
            "tolerance": "±1%",
            "power_rating": "0.125W",
            "temperature_coefficient": "±100ppm/°C",
        },
        "notes": "General purpose precision resistor",
    }


@pytest.fixture
def sample_storage_location_data():
    """
    Sample storage location data for tests
    """
    return {
        "name": "drawer-1",
        "description": "Main workbench drawer 1",
        "type": "drawer",
    }


# Remove test_user fixtures that depend on global_test_users
# Individual tests will create users as needed


@pytest.fixture
def auth_headers(client, db_session):
    """
    Create valid JWT token headers for authenticated requests (admin)
    Creates a fresh test user in the isolated test database
    """
    # Create a test admin user directly in the test database session
    admin_user = User(
        username="testadmin", full_name="Test Admin", is_admin=True, is_active=True
    )
    admin_user.set_password("testpassword")

    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)

    # Create JWT token for this user
    token = create_access_token(
        {
            "sub": admin_user.id,  # Use 'sub' as standard JWT claim for user ID
            "user_id": admin_user.id,  # Keep for backward compatibility
            "username": admin_user.username,
            "is_admin": admin_user.is_admin,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_auth_headers(client, db_session):
    """
    Create valid JWT token headers for regular user requests
    Creates a fresh regular test user in the isolated test database
    """
    # Create a test regular user directly in the test database session
    regular_user = User(
        username="testuser", full_name="Test User", is_admin=False, is_active=True
    )
    regular_user.set_password("testpassword")

    db_session.add(regular_user)
    db_session.commit()
    db_session.refresh(regular_user)

    # Create JWT token for this user
    token = create_access_token(
        {
            "sub": regular_user.id,  # Use 'sub' as standard JWT claim for user ID
            "user_id": regular_user.id,  # Keep for backward compatibility
            "username": regular_user.username,
            "is_admin": regular_user.is_admin,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def api_token_headers(auth_headers, client, db_session):
    """
    Create valid API token headers for authenticated requests
    Uses the same admin user created by auth_headers fixture
    """
    # Get the admin user that was created by auth_headers
    admin_user = db_session.query(User).filter(User.username == "testadmin").first()

    raw_token, api_token = APIToken.generate_token(
        user_id=admin_user.id, name="Test API Token", description="Token for testing"
    )
    db_session.add(api_token)
    db_session.commit()

    return {"Authorization": f"Bearer {raw_token}"}


@pytest.fixture
def auth_token(client, db_session):
    """
    Create JWT authentication token string for layout generator tests
    Creates a fresh test user in the isolated test database

    Returns: Raw JWT token string (not headers dict)
    """
    # Create a test admin user directly in the test database session
    test_user = User(
        username="layouttest",
        full_name="Layout Test User",
        is_admin=True,
        is_active=True,
    )
    test_user.set_password("testpassword")

    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)

    # Create JWT token for this user
    token = create_access_token(
        {
            "sub": test_user.id,
            "user_id": test_user.id,
            "username": test_user.username,
            "is_admin": test_user.is_admin,
        }
    )
    return token
