"""
Pytest configuration and shared fixtures
"""

import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.auth.jwt_auth import create_access_token
from src.database.connection import get_db
from src.main import app
from src.models import APIToken, User

# Set testing environment variables to ensure complete isolation
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"  # Use in-memory database for complete isolation
os.environ["PORT"] = "8005"  # Use different port for tests (production uses 8000)

# Test database URL - in-memory database for complete isolation
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
test_engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False
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
    Set up fresh in-memory test database for each test
    """
    # Use the correct Base from models package to create all tables
    from src.models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=test_engine)

    yield

    # Drop all tables after test for clean state
    ModelsBase.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a database session for each test
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# Remove global_test_users fixture to avoid duplicate user creation
# Individual test fixtures will create users as needed


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with shared test database session
    Following Testing Isolation principle - use same session for fixtures and API
    Includes auth dependency overrides for TestClient compatibility
    """
    from fastapi.security import HTTPAuthorizationCredentials
    from src.auth.dependencies import get_optional_user
    from src.auth.jwt_auth import get_current_user as get_user_from_token
    from src.models import User

    def override_get_db():
        yield db_session

    async def test_get_optional_user(
        credentials: HTTPAuthorizationCredentials = None,
        db = None
    ):
        """TestClient-compatible version of get_optional_user"""
        if not credentials:
            return None

        # Use the shared test database session
        test_db = db_session

        try:
            user_data = get_user_from_token(credentials.credentials)
            user = test_db.query(User).filter(User.id == user_data["user_id"]).first()
            if user and user.is_active:
                return {
                    "user_id": user.id,
                    "username": user.username,
                    "is_admin": user.is_admin,
                    "auth_type": "jwt"
                }
        except Exception:
            pass

        return None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_optional_user] = test_get_optional_user

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_component_data():
    """
    Sample component data for tests
    """
    return {
        "name": "Resistor 10kΩ 1% 0805",
        "part_number": "RC0805FR-0710KL",
        "manufacturer": "Yageo",
        "component_type": "resistor",
        "value": "10kΩ",
        "package": "0805",
        "quantity_on_hand": 100,
        "minimum_stock": 20,
        "specifications": {
            "resistance": "10kΩ",
            "tolerance": "±1%",
            "power_rating": "0.125W",
            "temperature_coefficient": "±100ppm/°C"
        },
        "notes": "General purpose precision resistor"
    }


@pytest.fixture
def sample_storage_location_data():
    """
    Sample storage location data for tests
    """
    return {
        "name": "drawer-1",
        "description": "Main workbench drawer 1",
        "location_type": "drawer",
        "is_single_part_only": False
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
        username="testadmin",
        full_name="Test Admin",
        is_admin=True,
        is_active=True
    )
    admin_user.set_password("testpassword")

    db_session.add(admin_user)
    db_session.commit()
    db_session.refresh(admin_user)

    # Create JWT token for this user
    token = create_access_token({
        "sub": admin_user.id,  # Use 'sub' as standard JWT claim for user ID
        "user_id": admin_user.id,  # Keep for backward compatibility
        "username": admin_user.username,
        "is_admin": admin_user.is_admin
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def user_auth_headers(client, db_session):
    """
    Create valid JWT token headers for regular user requests
    Creates a fresh regular test user in the isolated test database
    """
    # Create a test regular user directly in the test database session
    regular_user = User(
        username="testuser",
        full_name="Test User",
        is_admin=False,
        is_active=True
    )
    regular_user.set_password("testpassword")

    db_session.add(regular_user)
    db_session.commit()
    db_session.refresh(regular_user)

    # Create JWT token for this user
    token = create_access_token({
        "sub": regular_user.id,  # Use 'sub' as standard JWT claim for user ID
        "user_id": regular_user.id,  # Keep for backward compatibility
        "username": regular_user.username,
        "is_admin": regular_user.is_admin
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def api_token_headers(auth_headers, db_session):
    """
    Create valid API token headers for authenticated requests
    Uses the same admin user created by auth_headers fixture
    """
    # Get the admin user that was created by auth_headers
    admin_user = db_session.query(User).filter(User.username == "testadmin").first()

    raw_token, api_token = APIToken.generate_token(
        user_id=admin_user.id,
        name="Test API Token",
        description="Token for testing"
    )
    db_session.add(api_token)
    db_session.commit()

    return {"X-API-Key": raw_token}
