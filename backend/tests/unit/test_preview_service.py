"""
Unit tests for PreviewService.

Tests preview generation logic in isolation with mocked database.
Focuses on business logic for sample name extraction, validation integration,
and response formatting.

Test Coverage (T046):
- First 5 + last name extraction
- Total count calculation
- Warning/error aggregation from validator
- is_valid flag logic
- Integration with validator service

NOTE: Test isolation - uses in-memory SQLite from conftest.py fixtures
"""


from backend.src.models.storage_location import StorageLocation
from backend.src.schemas.location_layout import (
    LayoutConfiguration,
    LayoutType,
    RangeSpecification,
    RangeType,
)
from backend.src.services.preview_service import PreviewService


class TestGeneratePreview:
    """Test suite for generate_preview method."""

    def test_preview_small_layout(self, db_session):
        """Test preview for small layout (< 5 items)."""
        service = PreviewService(db_session)
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
        # Will generate: shelfa, shelfb, shelfc (3 items)

        preview = service.generate_preview(config)

        assert preview.is_valid is True
        assert preview.total_count == 3
        assert len(preview.sample_names) == 3
        assert preview.sample_names == ["shelfa", "shelfb", "shelfc"]
        assert preview.last_name == "shelfc"
        assert preview.errors == []
        assert preview.warnings == []

    def test_preview_exactly_5_items(self, db_session):
        """Test preview with exactly 5 items."""
        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="bin",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=5, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )
        # Will generate: bin1, bin2, bin3, bin4, bin5

        preview = service.generate_preview(config)

        assert preview.is_valid is True
        assert preview.total_count == 5
        assert len(preview.sample_names) == 5
        assert preview.sample_names == ["bin1", "bin2", "bin3", "bin4", "bin5"]
        assert preview.last_name == "bin5"
        assert preview.errors == []

    def test_preview_more_than_5_items(self, db_session):
        """Test preview shows first 5 when > 5 items exist (FR-013)."""
        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="drawer-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=10, zero_pad=False
                )
            ],
            separators=[],
            location_type="drawer",
            single_part_only=False,
        )
        # Will generate: drawer-1 through drawer-10 (10 items)

        preview = service.generate_preview(config)

        assert preview.is_valid is True
        assert preview.total_count == 10
        assert len(preview.sample_names) == 5
        assert preview.sample_names == [
            "drawer-1",
            "drawer-2",
            "drawer-3",
            "drawer-4",
            "drawer-5",
        ]
        assert preview.last_name == "drawer-10"
        assert preview.errors == []

    def test_preview_large_layout(self, db_session):
        """Test preview for large layout (many items)."""
        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="slot",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="e",
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
        # Total: 5 * 20 = 100 items

        preview = service.generate_preview(config)

        assert preview.is_valid is True
        assert preview.total_count == 100
        assert len(preview.sample_names) == 5
        assert preview.sample_names[0] == "slota-1"
        assert preview.sample_names[4] == "slota-5"
        assert preview.last_name == "slote-20"

    def test_preview_with_warning(self, db_session):
        """Test preview includes warnings for > 100 locations (FR-009)."""
        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="big",
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

        preview = service.generate_preview(config)

        assert preview.is_valid is True  # Still valid, just warning
        assert preview.total_count == 120
        assert len(preview.warnings) > 0
        assert any("cannot be undone" in w.lower() for w in preview.warnings)
        assert preview.errors == []

    def test_preview_with_validation_error(self, db_session):
        """Test preview shows errors when validation fails."""
        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="toobig",
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

        preview = service.generate_preview(config)

        assert preview.is_valid is False
        assert preview.total_count == 780  # Real count even when invalid (per FR-008)
        assert preview.sample_names == []
        assert preview.last_name == ""
        assert len(preview.errors) > 0
        assert any("500" in error for error in preview.errors)

    def test_preview_with_duplicate_error(self, db_session):
        """Test preview shows duplicate errors."""
        # Create existing locations
        existing = [
            StorageLocation(name="dup-a", type="bin"),
            StorageLocation(name="dup-b", type="bin"),
        ]
        db_session.add_all(existing)
        db_session.commit()

        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="dup-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="e",
                    capitalize=False,
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )

        preview = service.generate_preview(config)

        assert preview.is_valid is False
        assert preview.total_count == 5  # Real count even when duplicates exist
        assert preview.sample_names == []
        assert len(preview.errors) > 0
        assert any("duplicate" in error.lower() for error in preview.errors)

    def test_preview_single_layout(self, db_session):
        """Test preview for SINGLE layout (just prefix)."""
        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.SINGLE,
            prefix="main-room",
            ranges=[],
            separators=[],
            location_type="room",
            single_part_only=False,
        )

        preview = service.generate_preview(config)

        assert preview.is_valid is True
        assert preview.total_count == 1
        assert preview.sample_names == ["main-room"]
        assert preview.last_name == "main-room"
        assert preview.errors == []
        assert preview.warnings == []

    def test_preview_3d_grid_layout(self, db_session):
        """Test preview for GRID_3D layout."""
        service = PreviewService(db_session)
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
        # Total: 3 * 4 * 3 = 36

        preview = service.generate_preview(config)

        assert preview.is_valid is True
        assert preview.total_count == 36
        assert len(preview.sample_names) == 5
        assert preview.sample_names[0] == "racka-1-1"
        assert preview.last_name == "rackc-4-3"

    def test_preview_with_zero_padding(self, db_session):
        """Test preview shows zero-padded numbers correctly."""
        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="bin-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=100, zero_pad=True
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )

        preview = service.generate_preview(config)

        assert preview.is_valid is True
        assert preview.total_count == 100
        assert len(preview.sample_names) == 5
        assert preview.sample_names[0] == "bin-001"
        assert preview.sample_names[4] == "bin-005"
        assert preview.last_name == "bin-100"

    def test_preview_with_capitalization(self, db_session):
        """Test preview shows capitalized letters correctly."""
        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="SHELF-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="j",
                    capitalize=True,
                )
            ],
            separators=[],
            location_type="shelf",
            single_part_only=False,
        )

        preview = service.generate_preview(config)

        assert preview.is_valid is True
        assert preview.total_count == 10
        assert len(preview.sample_names) == 5
        assert preview.sample_names == [
            "SHELF-A",
            "SHELF-B",
            "SHELF-C",
            "SHELF-D",
            "SHELF-E",
        ]
        assert preview.last_name == "SHELF-J"


class TestPreviewEdgeCases:
    """Test edge cases and error scenarios."""

    def test_preview_with_parent_id_not_found(self, db_session):
        """Test preview accepts parent_id without validating existence.

        Parent validation only happens at creation time, not during preview.
        This follows FR-014 and integration test requirements.
        """
        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="child-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=5, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            parent_id="00000000-0000-0000-0000-000000000000",
            single_part_only=False,
        )

        preview = service.generate_preview(config)

        # Preview should succeed - parent validation only happens at creation time
        assert preview.is_valid is True
        assert len(preview.errors) == 0
        assert preview.total_count == 5

    def test_preview_with_valid_parent_id(self, db_session):
        """Test preview succeeds when parent_id exists."""
        # Create parent location
        parent = StorageLocation(name="parent-drawer", type="drawer")
        db_session.add(parent)
        db_session.commit()
        db_session.refresh(parent)

        service = PreviewService(db_session)
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

        preview = service.generate_preview(config)

        assert preview.is_valid is True
        assert preview.total_count == 5

    def test_preview_idempotent(self, db_session):
        """Test preview is idempotent (multiple calls produce same result)."""
        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="test-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=10, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )

        # Call preview multiple times
        preview1 = service.generate_preview(config)
        preview2 = service.generate_preview(config)
        preview3 = service.generate_preview(config)

        # All results should be identical
        assert preview1.sample_names == preview2.sample_names == preview3.sample_names
        assert preview1.last_name == preview2.last_name == preview3.last_name
        assert preview1.total_count == preview2.total_count == preview3.total_count
        assert preview1.is_valid == preview2.is_valid == preview3.is_valid

        # Database should be unchanged (no locations created)
        location_count = db_session.query(StorageLocation).count()
        assert location_count == 0

    def test_preview_no_side_effects(self, db_session):
        """Test preview has no side effects on database."""
        initial_count = db_session.query(StorageLocation).count()

        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="test",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="e",
                    capitalize=False,
                ),
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=10, zero_pad=False
                ),
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )

        preview = service.generate_preview(config)

        # Verify preview was generated
        assert preview.total_count == 50
        assert len(preview.sample_names) == 5

        # Verify no database changes
        final_count = db_session.query(StorageLocation).count()
        assert final_count == initial_count

    def test_preview_complex_real_world_example(self, db_session):
        """Test preview with realistic complex configuration."""
        service = PreviewService(db_session)
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
        # Workshop bins: WS-A-01 through WS-E-12 (60 total)

        preview = service.generate_preview(config)

        assert preview.is_valid is True
        assert preview.total_count == 60
        assert len(preview.sample_names) == 5
        assert preview.sample_names[0] == "WS-A-01"
        assert preview.sample_names[4] == "WS-A-05"
        assert preview.last_name == "WS-E-12"
        assert preview.errors == []
        assert preview.warnings == []  # 60 < 100, no warning


class TestPreviewValidationIntegration:
    """Test integration between PreviewService and LocationValidatorService."""

    def test_preview_uses_validator_for_errors(self, db_session):
        """Test preview correctly integrates validator errors."""
        # Create duplicate
        existing = StorageLocation(name="test-5", type="bin")
        db_session.add(existing)
        db_session.commit()

        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="test-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=10, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )

        preview = service.generate_preview(config)

        # Should have error from validator about duplicate
        assert preview.is_valid is False
        assert len(preview.errors) > 0
        assert any("duplicate" in error.lower() for error in preview.errors)
        assert any("test-5" in error for error in preview.errors)

    def test_preview_uses_validator_for_warnings(self, db_session):
        """Test preview correctly integrates validator warnings."""
        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="warn",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="e",
                    capitalize=False,
                ),  # 5
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=25, zero_pad=False
                ),  # 25
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )
        # Total: 5 * 25 = 125 > 100

        preview = service.generate_preview(config)

        # Should be valid with warning from validator
        assert preview.is_valid is True
        assert len(preview.warnings) > 0
        assert any("cannot be undone" in w.lower() for w in preview.warnings)
        assert preview.errors == []

    def test_preview_early_return_on_validation_error(self, db_session):
        """Test preview returns early when validation fails (no name generation)."""
        service = PreviewService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="invalid",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="z",
                    capitalize=False,
                ),  # 26
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=50, zero_pad=False
                ),  # 50
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )
        # Total: 26 * 50 = 1300 > 500 (invalid)

        preview = service.generate_preview(config)

        # Should return immediately with error, no names generated
        # But total_count should still be calculated (per FR-008 integration tests)
        assert preview.is_valid is False
        assert preview.total_count == 1300  # Real count even when validation fails
        assert preview.sample_names == []
        assert preview.last_name == ""
        assert len(preview.errors) > 0
