"""
Smoke test for LocationGenerator service.

This is a basic test to verify the implementation is functional.
Full test suite should be in test_location_generator.py (TDD Phase 3.3).
"""


import pytest

from backend.src.schemas.location_layout import (
    LayoutConfiguration,
    LayoutType,
    RangeSpecification,
    RangeType,
)
from backend.src.services.location_generator import LocationGeneratorService


@pytest.mark.unit
def test_generate_letter_range():
    """Test generating a letter range."""
    service = LocationGeneratorService()
    range_spec = RangeSpecification(
        range_type=RangeType.LETTERS, start="a", end="c", capitalize=False
    )
    result = list(service.generate_range(range_spec))
    assert result == ["a", "b", "c"]


@pytest.mark.unit
def test_generate_number_range():
    """Test generating a number range."""
    service = LocationGeneratorService()
    range_spec = RangeSpecification(
        range_type=RangeType.NUMBERS, start=1, end=3, zero_pad=False
    )
    result = list(service.generate_range(range_spec))
    assert result == ["1", "2", "3"]


@pytest.mark.unit
def test_generate_number_range_with_zero_padding():
    """Test generating a number range with zero padding."""
    service = LocationGeneratorService()
    range_spec = RangeSpecification(
        range_type=RangeType.NUMBERS, start=1, end=10, zero_pad=True
    )
    result = list(service.generate_range(range_spec))
    assert result == ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10"]


@pytest.mark.unit
def test_calculate_total_count_row():
    """Test calculating total count for row layout."""
    service = LocationGeneratorService()
    config = LayoutConfiguration(
        layout_type=LayoutType.ROW,
        prefix="box-",
        ranges=[RangeSpecification(range_type=RangeType.LETTERS, start="a", end="c")],
        separators=[],
        location_type="bin",
    )
    count = service.calculate_total_count(config)
    assert count == 3


@pytest.mark.unit
def test_calculate_total_count_grid():
    """Test calculating total count for grid layout."""
    service = LocationGeneratorService()
    config = LayoutConfiguration(
        layout_type=LayoutType.GRID,
        prefix="shelf-",
        ranges=[
            RangeSpecification(range_type=RangeType.LETTERS, start="a", end="c"),
            RangeSpecification(range_type=RangeType.NUMBERS, start=1, end=5),
        ],
        separators=["-"],
        location_type="shelf",
    )
    count = service.calculate_total_count(config)
    assert count == 15  # 3 letters * 5 numbers


@pytest.mark.unit
def test_generate_all_names_row():
    """Test generating all names for row layout."""
    service = LocationGeneratorService()
    config = LayoutConfiguration(
        layout_type=LayoutType.ROW,
        prefix="box-",
        ranges=[RangeSpecification(range_type=RangeType.LETTERS, start="a", end="c")],
        separators=[],
        location_type="bin",
    )
    names = service.generate_names(config)
    assert names == ["box-a", "box-b", "box-c"]


@pytest.mark.unit
def test_generate_all_names_grid():
    """Test generating all names for grid layout."""
    service = LocationGeneratorService()
    config = LayoutConfiguration(
        layout_type=LayoutType.GRID,
        prefix="shelf-",
        ranges=[
            RangeSpecification(range_type=RangeType.LETTERS, start="a", end="b"),
            RangeSpecification(range_type=RangeType.NUMBERS, start=1, end=2),
        ],
        separators=["-"],
        location_type="shelf",
    )
    names = service.generate_names(config)
    assert names == ["shelf-a-1", "shelf-a-2", "shelf-b-1", "shelf-b-2"]


@pytest.mark.unit
def test_generate_preview():
    """Test generating preview - uses PreviewService not LocationGeneratorService."""
    # Note: Preview functionality has been moved to PreviewService
    # This test validates that LocationGeneratorService generates names correctly
    service = LocationGeneratorService()
    config = LayoutConfiguration(
        layout_type=LayoutType.ROW,
        prefix="box-",
        ranges=[RangeSpecification(range_type=RangeType.LETTERS, start="a", end="f")],
        separators=[],
        location_type="bin",
    )

    # Generate all names and validate count
    names = service.generate_names(config)
    total_count = service.calculate_total_count(config)

    assert total_count == 6
    assert names == ["box-a", "box-b", "box-c", "box-d", "box-e", "box-f"]


@pytest.mark.unit
def test_validate_configuration_exceeds_limit():
    """Test validation - now handled by LocationValidatorService."""
    # Note: Validation has been moved to LocationValidatorService
    # This test just validates the generator can calculate counts correctly
    service = LocationGeneratorService()
    config = LayoutConfiguration(
        layout_type=LayoutType.ROW,
        prefix="test-",
        ranges=[RangeSpecification(range_type=RangeType.NUMBERS, start=1, end=600)],
        separators=[],
        location_type="bin",
    )

    count = service.calculate_total_count(config)
    assert count == 600  # Generator correctly calculates count


@pytest.mark.unit
def test_validate_configuration_warning_for_large_batch():
    """Test warning for large batches - now handled by LocationValidatorService."""
    # Note: Warning logic has been moved to LocationValidatorService
    # This test just validates the generator can calculate counts correctly
    service = LocationGeneratorService()
    config = LayoutConfiguration(
        layout_type=LayoutType.ROW,
        prefix="test-",
        ranges=[RangeSpecification(range_type=RangeType.NUMBERS, start=1, end=150)],
        separators=[],
        location_type="bin",
    )

    count = service.calculate_total_count(config)
    assert count == 150  # Generator correctly calculates count
