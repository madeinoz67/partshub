"""
Performance test for LocationGenerator service.

Tests that preview generation meets the <200ms requirement for 500 locations.
"""

import time

from backend.src.schemas.location_layout import (
    LayoutConfiguration,
    LayoutType,
    RangeSpecification,
    RangeType,
)
from backend.src.services.location_generator import LocationGeneratorService


def test_preview_performance_500_locations():
    """Test that name generation completes quickly for 500 locations."""
    service = LocationGeneratorService()

    # Create a config that generates exactly 500 locations (25 x 20 = 500)
    config = LayoutConfiguration(
        layout_type=LayoutType.GRID,
        prefix="test-",
        ranges=[
            RangeSpecification(
                range_type=RangeType.LETTERS, start="a", end="y"
            ),  # 25 letters
            RangeSpecification(
                range_type=RangeType.NUMBERS, start=1, end=20
            ),  # 20 numbers
        ],
        separators=["-"],
        location_type="bin",
    )

    start_time = time.time()
    names = service.generate_names(config)
    total_count = service.calculate_total_count(config)
    end_time = time.time()

    elapsed_ms = (end_time - start_time) * 1000

    # Verify correct results
    assert total_count == 500
    assert len(names) == 500
    assert names[0] == "test-a-1"
    assert names[-1] == "test-y-20"

    # Performance requirement: <200ms
    print(f"\nName generation for 500 locations: {elapsed_ms:.2f}ms")
    assert (
        elapsed_ms < 200
    ), f"Name generation took {elapsed_ms:.2f}ms, exceeding 200ms requirement"


def test_all_names_generation_performance():
    """Test full name generation for benchmarking."""
    service = LocationGeneratorService()

    # Generate 100 locations (10 x 10)
    config = LayoutConfiguration(
        layout_type=LayoutType.GRID,
        prefix="shelf-",
        ranges=[
            RangeSpecification(
                range_type=RangeType.LETTERS, start="a", end="j"
            ),  # 10 letters
            RangeSpecification(
                range_type=RangeType.NUMBERS, start=1, end=10
            ),  # 10 numbers
        ],
        separators=["-"],
        location_type="shelf",
    )

    start_time = time.time()
    names = service.generate_names(config)
    end_time = time.time()

    elapsed_ms = (end_time - start_time) * 1000

    assert len(names) == 100
    assert names[0] == "shelf-a-1"
    assert names[-1] == "shelf-j-10"

    print(f"\nFull generation for 100 locations: {elapsed_ms:.2f}ms")
