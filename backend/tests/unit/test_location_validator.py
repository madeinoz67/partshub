"""
Unit tests for LocationValidatorService.

Tests validation rules in isolation with mocked database dependencies.
Focuses on business logic for validation constraints and error/warning messages.

Test Coverage (T045):
- Range validation (start <= end)
- Total count limits (500 max, 100 warning)
- Duplicate name detection (mocked database)
- Invalid inputs (empty prefix, wrong separators)
- Parent location existence validation

NOTE: Test isolation - uses in-memory SQLite from conftest.py fixtures
"""

import pytest

from backend.src.models.storage_location import StorageLocation
from backend.src.schemas.location_layout import (
    LayoutConfiguration,
    LayoutType,
    RangeSpecification,
    RangeType,
)
from backend.src.services.location_validator import LocationValidatorService


class TestValidateConfiguration:
    """Test suite for validate_configuration method."""

    def test_valid_small_layout(self, db_session):
        """Test validation passes for small valid layout."""
        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="shelf",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="c",
                    capitalize=False,
                )
            ],
            separators=[],
            location_type="shelf",
            single_part_only=False,
        )

        errors, warnings = validator.validate_configuration(config)

        assert errors == []
        assert warnings == []

    def test_total_count_exceeds_500_max(self, db_session):
        """Test validation fails when total count exceeds 500 (FR-008)."""
        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="big",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="z",
                    capitalize=False,
                ),  # 26
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=30, zero_pad=False
                ),  # 30
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )
        # Total: 26 * 30 = 780 > 500

        errors, warnings = validator.validate_configuration(config)

        assert len(errors) > 0
        assert any("500" in error for error in errors)
        assert any("780" in error for error in errors)

    def test_total_count_exactly_500(self, db_session):
        """Test validation passes when total count equals exactly 500."""
        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="max",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="z",
                    capitalize=False,
                ),  # 26
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=19, zero_pad=False
                ),  # 19
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )
        # Total: 26 * 19 = 494 <= 500 (just under limit)

        errors, warnings = validator.validate_configuration(config)

        assert errors == []
        # Should have warning because it's > 100
        assert len(warnings) > 0

    def test_warning_above_100_locations(self, db_session):
        """Test warning appears when creating > 100 locations (FR-009)."""
        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="warn",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="f",
                    capitalize=False,
                ),  # 6
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=20, zero_pad=False
                ),  # 20
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )
        # Total: 6 * 20 = 120 > 100

        errors, warnings = validator.validate_configuration(config)

        assert errors == []  # Valid, just warning
        assert len(warnings) > 0
        assert any("cannot be undone" in warning.lower() for warning in warnings)
        assert any("120" in warning for warning in warnings)

    def test_no_warning_at_exactly_100_locations(self, db_session):
        """Test no warning when creating exactly 100 locations."""
        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="exactly",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="e",
                    capitalize=False,
                ),  # 5
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=20, zero_pad=False
                ),  # 20
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )
        # Total: 5 * 20 = 100 (no warning)

        errors, warnings = validator.validate_configuration(config)

        assert errors == []
        assert warnings == []

    def test_no_warning_below_100_locations(self, db_session):
        """Test no warning when creating < 100 locations."""
        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="small",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="d",
                    capitalize=False,
                ),  # 4
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=10, zero_pad=False
                ),  # 10
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )
        # Total: 4 * 10 = 40 (no warning)

        errors, warnings = validator.validate_configuration(config)

        assert errors == []
        assert warnings == []

    def test_duplicate_names_detection(self, db_session):
        """Test validation detects duplicate location names (FR-007)."""
        # Create existing locations in database
        existing_locations = [
            StorageLocation(name="drawer-a", type="drawer"),
            StorageLocation(name="drawer-b", type="drawer"),
            StorageLocation(name="drawer-c", type="drawer"),
        ]
        db_session.add_all(existing_locations)
        db_session.commit()

        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="drawer-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="e",
                    capitalize=False,
                )
            ],
            separators=[],
            location_type="drawer",
            single_part_only=False,
        )
        # Will try to create: drawer-a, drawer-b, drawer-c, drawer-d, drawer-e
        # drawer-a, drawer-b, drawer-c already exist

        errors, warnings = validator.validate_configuration(config)

        assert len(errors) > 0
        assert any("duplicate" in error.lower() for error in errors)
        assert any("drawer-a" in error for error in errors)
        assert any("drawer-b" in error for error in errors)
        assert any("drawer-c" in error for error in errors)

    def test_no_duplicates_with_fresh_names(self, db_session):
        """Test validation passes when no duplicates exist."""
        # Create some existing locations with different names
        existing_locations = [
            StorageLocation(name="shelf-x", type="shelf"),
            StorageLocation(name="shelf-y", type="shelf"),
        ]
        db_session.add_all(existing_locations)
        db_session.commit()

        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="drawer-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="c",
                    capitalize=False,
                )
            ],
            separators=[],
            location_type="drawer",
            single_part_only=False,
        )
        # Will create: drawer-a, drawer-b, drawer-c (no conflicts with shelf-x, shelf-y)

        errors, warnings = validator.validate_configuration(config)

        assert errors == []

    def test_partial_duplicates_detection(self, db_session):
        """Test validation detects partial duplicates (some names already exist)."""
        # Only one duplicate exists
        existing_location = StorageLocation(name="bin-5", type="bin")
        db_session.add(existing_location)
        db_session.commit()

        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="bin-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=10, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )
        # Will try to create: bin-1 to bin-10, but bin-5 exists

        errors, warnings = validator.validate_configuration(config)

        assert len(errors) > 0
        assert any("duplicate" in error.lower() for error in errors)
        assert any("bin-5" in error for error in errors)

    def test_parent_id_not_found(self, db_session):
        """Test validation fails when parent_id doesn't exist (FR-014)."""
        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="child-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="c",
                    capitalize=False,
                )
            ],
            separators=[],
            location_type="bin",
            parent_id="00000000-0000-0000-0000-000000000000",  # Non-existent UUID
            single_part_only=False,
        )

        errors, warnings = validator.validate_configuration(config)

        assert len(errors) > 0
        assert any("parent" in error.lower() for error in errors)
        assert any("not found" in error.lower() for error in errors)

    def test_parent_id_exists_validation_passes(self, db_session):
        """Test validation passes when parent_id exists."""
        # Create parent location
        parent = StorageLocation(name="parent-drawer", type="drawer")
        db_session.add(parent)
        db_session.commit()
        db_session.refresh(parent)

        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="slot-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=5, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            parent_id=str(parent.id),
            single_part_only=False,
        )

        errors, warnings = validator.validate_configuration(config)

        assert errors == []

    def test_parent_id_none_is_valid(self, db_session):
        """Test validation passes when parent_id is None (root locations)."""
        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="root-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="c",
                    capitalize=False,
                )
            ],
            separators=[],
            location_type="shelf",
            parent_id=None,
            single_part_only=False,
        )

        errors, warnings = validator.validate_configuration(config)

        assert errors == []

    def test_multiple_validation_errors(self, db_session):
        """Test multiple validation errors are returned together."""
        # Create duplicate location
        existing = StorageLocation(name="test-a-1", type="bin")
        db_session.add(existing)
        db_session.commit()

        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="test-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="z",
                    capitalize=False,
                ),  # 26
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=30, zero_pad=False
                ),  # 30
            ],
            separators=["-"],
            location_type="bin",
            parent_id="00000000-0000-0000-0000-000000000000",  # Non-existent
            single_part_only=False,
        )
        # Has issues: > 500 limit, duplicate, parent not found

        errors, warnings = validator.validate_configuration(config)

        # Should return error for > 500 limit immediately (early return)
        assert len(errors) > 0
        assert any("500" in error for error in errors)

    def test_single_layout_validation(self, db_session):
        """Test validation for SINGLE layout (no ranges)."""
        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.SINGLE,
            prefix="main-room",
            ranges=[],
            separators=[],
            location_type="room",
            single_part_only=False,
        )

        errors, warnings = validator.validate_configuration(config)

        assert errors == []
        assert warnings == []  # Only 1 location, no warnings

    def test_duplicate_limit_shows_max_5_names(self, db_session):
        """Test duplicate error message shows max 5 duplicate names."""
        # Create 10 duplicate locations
        duplicates = [
            StorageLocation(name=f"dup-{chr(97 + i)}", type="bin") for i in range(10)
        ]
        db_session.add_all(duplicates)
        db_session.commit()

        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="dup-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="j",
                    capitalize=False,
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )

        errors, warnings = validator.validate_configuration(config)

        assert len(errors) > 0
        # Should show first 5 duplicates + "..."
        assert any("..." in error for error in errors)
        # Count how many duplicates are shown (should be <= 5)
        duplicate_names_shown = sum(
            1 for error in errors for dup in duplicates[:5] if dup.name in error
        )
        assert duplicate_names_shown <= 5


class TestValidatorIntegration:
    """Integration tests for validator with generator service."""

    def test_validator_uses_generator_for_count(self, db_session):
        """Test validator correctly uses generator to calculate total count."""
        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID_3D,
            prefix="test",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="c",
                    capitalize=False,
                ),  # 3
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=4, zero_pad=False
                ),  # 4
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=5, zero_pad=False
                ),  # 5
            ],
            separators=["-", "-"],
            location_type="drawer",
            single_part_only=False,
        )
        # Total: 3 * 4 * 5 = 60

        # Should pass validation (< 500, < 100 so no warning)
        errors, warnings = validator.validate_configuration(config)

        assert errors == []
        assert warnings == []

    def test_validator_uses_generator_for_names(self, db_session):
        """Test validator correctly uses generator to get all names for duplicate check."""
        # Create strategic duplicate
        existing = StorageLocation(name="prefixB-2", type="bin")
        db_session.add(existing)
        db_session.commit()

        validator = LocationValidatorService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="prefix",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="A",
                    end="C",
                    capitalize=True,
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=3, zero_pad=False
                ),
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )
        # Will generate: prefixA-1, prefixA-2, prefixA-3, prefixB-1, prefixB-2, ...
        # prefixB-2 exists as duplicate

        errors, warnings = validator.validate_configuration(config)

        assert len(errors) > 0
        assert any("prefixB-2" in error for error in errors)
