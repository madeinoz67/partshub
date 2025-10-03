"""
Performance test for LocationGenerator service.

Tests that preview generation meets the <200ms requirement for 500 locations.
"""

import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.src.database import Base
from backend.src.services.location_generator import LocationGeneratorService


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()
    yield session
    session.close()


def test_preview_performance_500_locations(db_session):
    """Test that preview generation completes in <200ms for 500 locations."""
    service = LocationGeneratorService(db_session)

    # Create a config that generates exactly 500 locations (25 x 20 = 500)
    ranges = [
        {"range_type": "letters", "start": "a", "end": "y"},  # 25 letters
        {"range_type": "numbers", "start": 1, "end": 20},  # 20 numbers
    ]

    start_time = time.time()
    preview = service.generate_preview("test-", ranges, ["-"])
    end_time = time.time()

    elapsed_ms = (end_time - start_time) * 1000

    # Verify correct results
    assert preview["total_count"] == 500
    assert len(preview["sample_names"]) == 5
    assert preview["sample_names"][0] == "test-a-1"
    assert preview["last_name"] == "test-y-20"

    # Performance requirement: <200ms
    print(f"\nPreview generation for 500 locations: {elapsed_ms:.2f}ms")
    assert (
        elapsed_ms < 200
    ), f"Preview generation took {elapsed_ms:.2f}ms, exceeding 200ms requirement"


def test_all_names_generation_performance(db_session):
    """Test full name generation for benchmarking."""
    service = LocationGeneratorService(db_session)

    # Generate 100 locations (10 x 10)
    ranges = [
        {"range_type": "letters", "start": "a", "end": "j"},  # 10 letters
        {"range_type": "numbers", "start": 1, "end": 10},  # 10 numbers
    ]

    start_time = time.time()
    names = service.generate_all_names("shelf-", ranges, ["-"])
    end_time = time.time()

    elapsed_ms = (end_time - start_time) * 1000

    assert len(names) == 100
    assert names[0] == "shelf-a-1"
    assert names[-1] == "shelf-j-10"

    print(f"\nFull generation for 100 locations: {elapsed_ms:.2f}ms")
