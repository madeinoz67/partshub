"""
Pytest configuration and shared fixtures
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.connection import Base, get_db
from src.main import app

# Test database URL - in-memory SQLite
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine
engine = create_engine(
    TEST_DATABASE_URL,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
    echo=False
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """
    Create a fresh database session for each test
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """
    Create a test client with overridden database dependency
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

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