"""
Unit tests for LocationGenerator service.

These tests validate the core business logic for generating storage location names
BEFORE implementation. All tests MUST FAIL initially (TDD).

Test Coverage (T012-T022):
- T012: Letter range generation (a-z)
- T013: Number range generation (0-999)
- T014: Letter capitalization
- T015: Number zero-padding
- T016: Row layout (1D)
- T017: Grid layout (2D)
- T018: 3D grid layout
- T019: Preview generation (first 5, last 1)
- T020: Validation - max 500 locations
- T021: Validation - duplicate detection
- T022: Validation - start <= end

NOTE: Test isolation - each test uses in-memory SQLite database
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.src.database import Base


class TestLocationGenerator:
    """Unit tests for LocationGenerator service (does not exist yet - TDD)"""

    @pytest.fixture
    def db_session(self):
        """
        Create isolated in-memory SQLite database for each test.

        CRITICAL: This ensures Constitution Principle VI (Test Isolation).
        Each test gets fresh database instance with no shared state.
        """
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    @pytest.fixture
    def location_generator(self, db_session):
        """
        Create LocationGeneratorService instance for testing.
        """
        from backend.src.services.location_generator import LocationGeneratorService

        return LocationGeneratorService(db_session)

    def test_generate_letter_range(self, location_generator):
        """
        T012: FR-010 - Generate letter range (a-z)
        """
        # Test basic letter range
        result = list(location_generator.generate_range(
            range_type="letters",
            start="a",
            end="f",
            capitalize=False,
            zero_pad=False
        ))

        assert result == ["a", "b", "c", "d", "e", "f"], "Should generate a-f"

        # Test partial range
        result = list(location_generator.generate_range(
            range_type="letters",
            start="m",
            end="p",
            capitalize=False,
            zero_pad=False
        ))

        assert result == ["m", "n", "o", "p"], "Should generate m-p"

    def test_generate_number_range(self, location_generator):
        """
        T013: FR-011 - Generate number range (0-999)
        """
        # Test basic number range
        result = list(location_generator.generate_range(
            range_type="numbers",
            start=1,
            end=5,
            capitalize=False,
            zero_pad=False
        ))

        assert result == ["1", "2", "3", "4", "5"], "Should generate 1-5"

        # Test range starting from 0
        result = list(location_generator.generate_range(
            range_type="numbers",
            start=0,
            end=3,
            capitalize=False,
            zero_pad=False
        ))

        assert result == ["0", "1", "2", "3"], "Should generate 0-3"

    def test_letter_capitalization(self, location_generator):
        """
        T014: FR-010 - Letter ranges support capitalization
        """
        # Test lowercase (default)
        result = list(location_generator.generate_range(
            range_type="letters",
            start="a",
            end="c",
            capitalize=False,
            zero_pad=False
        ))

        assert result == ["a", "b", "c"], "Should generate lowercase letters"

        # Test uppercase
        result = list(location_generator.generate_range(
            range_type="letters",
            start="a",
            end="c",
            capitalize=True,
            zero_pad=False
        ))

        assert result == ["A", "B", "C"], "Should generate uppercase letters"

    def test_number_zero_padding(self, location_generator):
        """
        T015: FR-011 - Number ranges support zero-padding
        """
        # Test without zero-padding
        result = list(location_generator.generate_range(
            range_type="numbers",
            start=1,
            end=15,
            capitalize=False,
            zero_pad=False
        ))

        assert result[0] == "1", "First should be '1' without padding"
        assert result[-1] == "15", "Last should be '15'"

        # Test with zero-padding
        result = list(location_generator.generate_range(
            range_type="numbers",
            start=1,
            end=15,
            capitalize=False,
            zero_pad=True
        ))

        assert result[0] == "01", "First should be '01' with padding"
        assert result[4] == "05", "Fifth should be '05' with padding"
        assert result[-1] == "15", "Last should be '15' with padding"

    def test_row_layout_generation(self, location_generator):
        """
        T016: FR-002 - Row layout (1D) generation
        """
        prefix = "box1-"
        ranges = [
            {"range_type": "letters", "start": "a", "end": "f", "capitalize": False, "zero_pad": False}
        ]
        separators = []

        result = location_generator.generate_all_names(prefix, ranges, separators)

        assert len(result) == 6, "Should generate 6 locations"
        assert result == ["box1-a", "box1-b", "box1-c", "box1-d", "box1-e", "box1-f"]

    def test_grid_layout_generation(self, location_generator):
        """
        T017: FR-003 - Grid layout (2D) generation
        """
        prefix = "shelf-"
        ranges = [
            {"range_type": "letters", "start": "a", "end": "c", "capitalize": False, "zero_pad": False},
            {"range_type": "numbers", "start": 1, "end": 3, "capitalize": False, "zero_pad": False}
        ]
        separators = ["-"]

        result = location_generator.generate_all_names(prefix, ranges, separators)

        assert len(result) == 9, "Should generate 9 locations (3x3)"
        assert result[0] == "shelf-a-1", "First should be shelf-a-1"
        assert result[1] == "shelf-a-2", "Second should be shelf-a-2"
        assert result[2] == "shelf-a-3", "Third should be shelf-a-3"
        assert result[3] == "shelf-b-1", "Fourth should be shelf-b-1"
        assert result[-1] == "shelf-c-3", "Last should be shelf-c-3"

    def test_3d_grid_layout_generation(self, location_generator):
        """
        T018: FR-004 - 3D grid layout generation
        """
        prefix = "warehouse-"
        ranges = [
            {"range_type": "letters", "start": "a", "end": "b", "capitalize": False, "zero_pad": False},
            {"range_type": "numbers", "start": 1, "end": 2, "capitalize": False, "zero_pad": False},
            {"range_type": "numbers", "start": 1, "end": 2, "capitalize": False, "zero_pad": False}
        ]
        separators = ["-", "."]

        result = location_generator.generate_all_names(prefix, ranges, separators)

        assert len(result) == 8, "Should generate 8 locations (2x2x2)"
        assert result[0] == "warehouse-a-1.1", "First should be warehouse-a-1.1"
        assert result[1] == "warehouse-a-1.2", "Second should be warehouse-a-1.2"
        assert result[2] == "warehouse-a-2.1", "Third should be warehouse-a-2.1"
        assert result[3] == "warehouse-a-2.2", "Fourth should be warehouse-a-2.2"
        assert result[4] == "warehouse-b-1.1", "Fifth should be warehouse-b-1.1"
        assert result[-1] == "warehouse-b-2.2", "Last should be warehouse-b-2.2"

    def test_preview_generation(self, location_generator):
        """
        T019: FR-013 - Preview shows first 5 and last name
        """
        prefix = "drawer-"
        ranges = [
            {"range_type": "letters", "start": "a", "end": "f", "capitalize": False, "zero_pad": False},
            {"range_type": "numbers", "start": 1, "end": 5, "capitalize": False, "zero_pad": False}
        ]
        separators = ["-"]

        preview = location_generator.generate_preview(prefix, ranges, separators)

        assert "sample_names" in preview, "Preview should have sample_names"
        assert "last_name" in preview, "Preview should have last_name"
        assert "total_count" in preview, "Preview should have total_count"

        assert len(preview["sample_names"]) == 5, "Should show first 5 names"
        assert preview["sample_names"][0] == "drawer-a-1", "First sample should be drawer-a-1"
        assert preview["last_name"] == "drawer-f-5", "Last name should be drawer-f-5"
        assert preview["total_count"] == 30, "Total should be 30 (6x5)"

    def test_validation_max_500_locations(self, location_generator):
        """
        T020: FR-008 - Validation enforces max 500 locations
        """
        config = {
            "layout_type": "grid",
            "prefix": "big-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "z", "capitalize": False, "zero_pad": False},  # 26
                {"range_type": "numbers", "start": 1, "end": 30, "capitalize": False, "zero_pad": False}      # 30
            ],
            "separators": ["-"]
        }
        # Total: 26 * 30 = 780 > 500

        is_valid, errors, warnings = location_generator.validate_configuration(config)

        assert is_valid is False, "Should be invalid (780 > 500)"
        assert len(errors) > 0, "Should have validation errors"
        assert any("500" in error for error in errors), "Should mention 500 limit"

        # Verify total count calculation is correct
        total_count = location_generator.calculate_total_count(config.get("ranges", []))
        assert total_count == 780, "Should calculate total correctly"

    def test_validation_duplicate_detection(self, location_generator, db_session):
        """
        T021: FR-007 - Validation detects duplicate names
        """
        # First, create some existing locations in database
        from backend.src.models.storage_location import StorageLocation
        import uuid

        existing = [
            StorageLocation(
                id=str(uuid.uuid4()),
                name="test-a",
                type="bin",
                location_hierarchy="test-a"
            ),
            StorageLocation(
                id=str(uuid.uuid4()),
                name="test-b",
                type="bin",
                location_hierarchy="test-b"
            )
        ]
        db_session.add_all(existing)
        db_session.commit()

        # Try to generate locations with overlapping names
        config = {
            "layout_type": "row",
            "prefix": "test-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c", "capitalize": False, "zero_pad": False}
            ],
            "separators": [],
            "location_type": "bin"
        }

        is_valid, errors, warnings = location_generator.validate_configuration(config)

        assert is_valid is False, "Should be invalid (duplicates exist)"
        assert len(errors) > 0, "Should have validation errors"
        assert any("already exist" in error.lower() for error in errors), "Should mention duplicates"
        assert any("test-a" in error for error in errors), "Should list duplicate name test-a"

    def test_validation_start_less_than_end(self, location_generator):
        """
        T022: FR-019 - Validation ensures start <= end
        """
        # Test invalid letter range - should raise ValueError in generate_range
        with pytest.raises(ValueError) as exc_info:
            list(location_generator.generate_range(
                range_type="letters",
                start="z",
                end="a",
                capitalize=False,
                zero_pad=False
            ))
        assert "Invalid letter range" in str(exc_info.value), "Should mention invalid range"

        # Test invalid number range - should raise ValueError in generate_range
        with pytest.raises(ValueError) as exc_info:
            list(location_generator.generate_range(
                range_type="numbers",
                start=99,
                end=1,
                capitalize=False,
                zero_pad=False
            ))
        assert "Invalid number range" in str(exc_info.value), "Should mention invalid range"

    def test_validation_warning_above_100_locations(self, location_generator):
        """
        T022.1: FR-009 - Warning when creating > 100 locations (bonus test)
        """
        config = {
            "layout_type": "grid",
            "prefix": "warn-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "f", "capitalize": False, "zero_pad": False},  # 6
                {"range_type": "numbers", "start": 1, "end": 20, "capitalize": False, "zero_pad": False}     # 20
            ],
            "separators": ["-"],
            "location_type": "bin"
        }
        # Total: 6 * 20 = 120 > 100

        is_valid, errors, warnings = location_generator.validate_configuration(config)

        assert is_valid is True, "Should be valid (120 < 500)"
        assert len(warnings) > 0, "Should have warnings"
        assert any("cannot be undone" in w.lower() for w in warnings), "Should warn about irreversibility"

        # Verify total count calculation
        total_count = location_generator.calculate_total_count(config.get("ranges", []))
        assert total_count == 120, "Should calculate total correctly"
