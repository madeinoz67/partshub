"""
Unit tests for LocationGeneratorService.

Tests name generation algorithms in isolation without database dependencies.
Focuses on business logic for range generation, Cartesian products, and edge cases.

Test Coverage (T044):
- Letter range generation (a-z, capitalization)
- Number range generation (0-999, zero-padding)
- Cartesian product combinations
- Edge cases (single item, max range)
- All layout types (SINGLE, ROW, GRID, GRID_3D)

NOTE: Test isolation - pure business logic, no database dependencies
"""

import pytest

from backend.src.schemas.location_layout import (
    LayoutConfiguration,
    LayoutType,
    RangeSpecification,
    RangeType,
)
from backend.src.services.location_generator import LocationGeneratorService


class TestGenerateRange:
    """Test suite for generate_range method."""

    def test_letter_range_lowercase(self):
        """Test generating lowercase letter range."""
        service = LocationGeneratorService()
        range_spec = RangeSpecification(
            range_type=RangeType.LETTERS,
            start="a",
            end="e",
            capitalize=False,
        )

        result = list(service.generate_range(range_spec))

        assert result == ["a", "b", "c", "d", "e"]

    def test_letter_range_uppercase(self):
        """Test generating uppercase letter range with capitalize=True."""
        service = LocationGeneratorService()
        range_spec = RangeSpecification(
            range_type=RangeType.LETTERS,
            start="a",
            end="d",
            capitalize=True,
        )

        result = list(service.generate_range(range_spec))

        assert result == ["A", "B", "C", "D"]

    def test_letter_range_single_character(self):
        """Test letter range with single character (start == end)."""
        service = LocationGeneratorService()
        range_spec = RangeSpecification(
            range_type=RangeType.LETTERS,
            start="m",
            end="m",
            capitalize=False,
        )

        result = list(service.generate_range(range_spec))

        assert result == ["m"]

    def test_letter_range_full_alphabet(self):
        """Test generating full alphabet (a-z)."""
        service = LocationGeneratorService()
        range_spec = RangeSpecification(
            range_type=RangeType.LETTERS,
            start="a",
            end="z",
            capitalize=False,
        )

        result = list(service.generate_range(range_spec))

        assert len(result) == 26
        assert result[0] == "a"
        assert result[-1] == "z"

    def test_number_range_no_padding(self):
        """Test generating number range without zero padding."""
        service = LocationGeneratorService()
        range_spec = RangeSpecification(
            range_type=RangeType.NUMBERS,
            start=1,
            end=5,
            zero_pad=False,
        )

        result = list(service.generate_range(range_spec))

        assert result == ["1", "2", "3", "4", "5"]

    def test_number_range_with_padding(self):
        """Test generating number range with zero padding."""
        service = LocationGeneratorService()
        range_spec = RangeSpecification(
            range_type=RangeType.NUMBERS,
            start=1,
            end=100,
            zero_pad=True,
        )

        result = list(service.generate_range(range_spec))

        # Check padding based on end value (100 has 3 digits)
        assert result[0] == "001"
        assert result[9] == "010"
        assert result[99] == "100"
        assert len(result) == 100

    def test_number_range_zero_to_nine_with_padding(self):
        """Test number range 0-9 with zero padding."""
        service = LocationGeneratorService()
        range_spec = RangeSpecification(
            range_type=RangeType.NUMBERS,
            start=0,
            end=9,
            zero_pad=True,
        )

        result = list(service.generate_range(range_spec))

        # Padding width should be 1 digit (based on '9')
        assert result == ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

    def test_number_range_single_number(self):
        """Test number range with single value (start == end)."""
        service = LocationGeneratorService()
        range_spec = RangeSpecification(
            range_type=RangeType.NUMBERS,
            start=42,
            end=42,
            zero_pad=False,
        )

        result = list(service.generate_range(range_spec))

        assert result == ["42"]

    def test_number_range_max_range(self):
        """Test number range at maximum (0-999)."""
        service = LocationGeneratorService()
        range_spec = RangeSpecification(
            range_type=RangeType.NUMBERS,
            start=0,
            end=999,
            zero_pad=False,
        )

        result = list(service.generate_range(range_spec))

        assert len(result) == 1000
        assert result[0] == "0"
        assert result[-1] == "999"


class TestCalculateTotalCount:
    """Test suite for calculate_total_count method."""

    def test_single_layout_count(self):
        """Test total count for SINGLE layout (no ranges)."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.SINGLE,
            prefix="main",
            ranges=[],
            separators=[],
            location_type="room",
            single_part_only=False,
        )

        result = service.calculate_total_count(config)

        assert result == 1

    def test_row_layout_count_letters(self):
        """Test total count for ROW layout with letter range."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="shelf",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="f",
                    capitalize=False,
                )
            ],
            separators=[],
            location_type="shelf",
            single_part_only=False,
        )

        result = service.calculate_total_count(config)

        assert result == 6  # a-f = 6 locations

    def test_row_layout_count_numbers(self):
        """Test total count for ROW layout with number range."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="bin",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=20, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )

        result = service.calculate_total_count(config)

        assert result == 20  # 1-20 = 20 locations

    def test_grid_layout_count(self):
        """Test total count for GRID layout (2D)."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="drawer",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="d",
                    capitalize=False,
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=5, zero_pad=False
                ),
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )

        result = service.calculate_total_count(config)

        assert result == 20  # 4 letters * 5 numbers = 20 locations

    def test_grid_3d_layout_count(self):
        """Test total count for GRID_3D layout (3D)."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID_3D,
            prefix="rack",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="c",
                    capitalize=False,
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=4, zero_pad=False
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=3, zero_pad=False
                ),
            ],
            separators=["-", "-"],
            location_type="drawer",
            single_part_only=False,
        )

        result = service.calculate_total_count(config)

        assert result == 36  # 3 letters * 4 numbers * 3 numbers = 36 locations

    def test_large_grid_count(self):
        """Test total count for large grid (approaching max limit)."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="storage",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="z",
                    capitalize=False,
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=20, zero_pad=False
                ),
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )

        result = service.calculate_total_count(config)

        assert result == 520  # 26 letters * 20 numbers = 520 locations


class TestGenerateNames:
    """Test suite for generate_names method."""

    def test_single_layout_names(self):
        """Test name generation for SINGLE layout (just prefix)."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.SINGLE,
            prefix="main",
            ranges=[],
            separators=[],
            location_type="room",
            single_part_only=False,
        )

        result = service.generate_names(config)

        assert result == ["main"]

    def test_row_layout_letters(self):
        """Test name generation for ROW layout with letters."""
        service = LocationGeneratorService()
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

        result = service.generate_names(config)

        assert result == ["shelfa", "shelfb", "shelfc"]

    def test_row_layout_numbers(self):
        """Test name generation for ROW layout with numbers."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="bin",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=3, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )

        result = service.generate_names(config)

        assert result == ["bin1", "bin2", "bin3"]

    def test_row_layout_no_separator(self):
        """Test ROW layout concatenates prefix and range directly."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="drawer",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=2, zero_pad=False
                )
            ],
            separators=[],  # ROW layout has 0 separators
            location_type="drawer",
            single_part_only=False,
        )

        result = service.generate_names(config)

        # No separator between prefix and number
        assert result == ["drawer1", "drawer2"]

    def test_grid_layout_cartesian_product(self):
        """Test GRID layout with Cartesian product of two ranges."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="box",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="b",
                    capitalize=True,
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=2, zero_pad=False
                ),
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )

        result = service.generate_names(config)

        # Cartesian product: A1, A2, B1, B2
        assert result == ["boxA-1", "boxA-2", "boxB-1", "boxB-2"]

    def test_grid_layout_with_zero_padding(self):
        """Test GRID layout with zero-padded numbers."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="rack",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="b",
                    capitalize=False,
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=10, zero_pad=True
                ),
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )

        result = service.generate_names(config)

        # Check first and last names with padding
        assert result[0] == "racka-01"
        assert result[9] == "racka-10"
        assert result[10] == "rackb-01"
        assert len(result) == 20

    def test_grid_3d_layout(self):
        """Test GRID_3D layout with three ranges."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID_3D,
            prefix="shelf",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="b",
                    capitalize=False,
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=2, zero_pad=False
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=2, zero_pad=False,
                ),
            ],
            separators=["-", "-"],
            location_type="drawer",
            single_part_only=False,
        )

        result = service.generate_names(config)

        # 3D Cartesian product with separators: shelfa-1-1, shelfa-1-2, shelfa-2-1, shelfa-2-2, shelfb-1-1, shelfb-1-2, shelfb-2-1, shelfb-2-2
        assert len(result) == 8
        assert result[0] == "shelfa-1-1"
        assert result[1] == "shelfa-1-2"
        assert result[2] == "shelfa-2-1"
        assert result[-1] == "shelfb-2-2"

    def test_grid_3d_with_multiple_separators(self):
        """Test GRID_3D layout with different separators."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID_3D,
            prefix="loc",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="x",
                    end="y",
                    capitalize=True,
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=2, zero_pad=False
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=2, zero_pad=False
                ),
            ],
            separators=[":", "."],
            location_type="shelf",
            single_part_only=False,
        )

        result = service.generate_names(config)

        # Different separators between ranges
        assert result[0] == "locX:1.1"
        assert result[-1] == "locY:2.2"

    def test_whitespace_prefix_stripped(self):
        """Test prefix whitespace is handled correctly."""
        service = LocationGeneratorService()
        # Prefix will be stripped by schema validation
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="  test  ",  # Whitespace will be stripped to "test"
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
            single_part_only=False,
        )

        result = service.generate_names(config)

        # Prefix should be stripped
        assert result == ["testa", "testb", "testc"]

    def test_complex_real_world_example(self):
        """Test realistic complex example (workshop rack system)."""
        service = LocationGeneratorService()
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="WS-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="e",
                    capitalize=True,
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=12, zero_pad=True
                ),
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )

        result = service.generate_names(config)

        # Workshop bins: WS-A-01 through WS-E-12
        assert len(result) == 60  # 5 * 12
        assert result[0] == "WS-A-01"
        assert result[11] == "WS-A-12"
        assert result[12] == "WS-B-01"
        assert result[-1] == "WS-E-12"
