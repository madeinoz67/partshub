"""
Smoke test for LocationGenerator service.

This is a basic test to verify the implementation is functional.
Full test suite should be in test_location_generator.py (TDD Phase 3.3).
"""

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
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_generate_letter_range():
    """Test generating a letter range."""
    service = LocationGeneratorService(None)
    result = list(service.generate_range("letters", "a", "c", capitalize=False))
    assert result == ["a", "b", "c"]


def test_generate_number_range():
    """Test generating a number range."""
    service = LocationGeneratorService(None)
    result = list(service.generate_range("numbers", 1, 3, zero_pad=False))
    assert result == ["1", "2", "3"]


def test_generate_number_range_with_zero_padding():
    """Test generating a number range with zero padding."""
    service = LocationGeneratorService(None)
    result = list(service.generate_range("numbers", 1, 10, zero_pad=True))
    assert result == ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]


def test_calculate_total_count_row():
    """Test calculating total count for row layout."""
    service = LocationGeneratorService(None)
    ranges = [{"range_type": "letters", "start": "a", "end": "c"}]
    count = service.calculate_total_count(ranges)
    assert count == 3


def test_calculate_total_count_grid():
    """Test calculating total count for grid layout."""
    service = LocationGeneratorService(None)
    ranges = [
        {"range_type": "letters", "start": "a", "end": "c"},
        {"range_type": "numbers", "start": 1, "end": 5},
    ]
    count = service.calculate_total_count(ranges)
    assert count == 15  # 3 letters * 5 numbers


def test_generate_all_names_row():
    """Test generating all names for row layout."""
    service = LocationGeneratorService(None)
    ranges = [{"range_type": "letters", "start": "a", "end": "c"}]
    names = service.generate_all_names("box-", ranges, [])
    assert names == ["box-a", "box-b", "box-c"]


def test_generate_all_names_grid():
    """Test generating all names for grid layout."""
    service = LocationGeneratorService(None)
    ranges = [
        {"range_type": "letters", "start": "a", "end": "b"},
        {"range_type": "numbers", "start": 1, "end": 2},
    ]
    names = service.generate_all_names("shelf-", ranges, ["-"])
    assert names == ["shelf-a-1", "shelf-a-2", "shelf-b-1", "shelf-b-2"]


def test_generate_preview(db_session):
    """Test generating preview."""
    service = LocationGeneratorService(db_session)
    ranges = [{"range_type": "letters", "start": "a", "end": "f"}]
    preview = service.generate_preview("box-", ranges, [])

    assert len(preview["sample_names"]) == 5
    assert preview["sample_names"] == ["box-a", "box-b", "box-c", "box-d", "box-e"]
    assert preview["last_name"] == "box-f"
    assert preview["total_count"] == 6


def test_validate_configuration_exceeds_limit(db_session):
    """Test validation fails when exceeding 500 locations."""
    service = LocationGeneratorService(db_session)
    config = {
        "prefix": "test-",
        "ranges": [
            {"range_type": "numbers", "start": 1, "end": 600},  # 600 locations
        ],
        "separators": [],
    }

    is_valid, errors, warnings = service.validate_configuration(config)

    assert not is_valid
    assert len(errors) > 0
    assert "500" in errors[0]


def test_validate_configuration_warning_for_large_batch(db_session):
    """Test warning is generated for batches over 100."""
    service = LocationGeneratorService(db_session)
    config = {
        "prefix": "test-",
        "ranges": [
            {"range_type": "numbers", "start": 1, "end": 150},  # 150 locations
        ],
        "separators": [],
    }

    is_valid, errors, warnings = service.validate_configuration(config)

    assert is_valid
    assert len(warnings) > 0
    assert "150" in warnings[0]
