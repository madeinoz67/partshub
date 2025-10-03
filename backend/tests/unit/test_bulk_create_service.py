"""
Unit tests for BulkCreateService.

Tests bulk creation logic with database transactions.
Focuses on business logic for transactional creation, rollback on errors,
and proper persistence of location data.

Test Coverage (T047):
- Successful bulk creation
- Transaction rollback on error
- layout_config persistence
- parent_id assignment
- Duplicate handling
- All-or-nothing semantics

NOTE: Test isolation - uses in-memory SQLite from conftest.py fixtures
"""


from backend.src.models.storage_location import StorageLocation
from backend.src.schemas.location_layout import (
    LayoutConfiguration,
    LayoutType,
    RangeSpecification,
    RangeType,
)
from backend.src.services.bulk_create_service import BulkCreateService


class TestBulkCreateLocations:
    """Test suite for bulk_create_locations method."""

    def test_successful_small_batch_creation(self, db_session):
        """Test successful creation of small batch of locations."""
        service = BulkCreateService(db_session)
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

        response = service.bulk_create_locations(config)

        assert response.success is True
        assert response.created_count == 3
        assert len(response.created_ids) == 3
        assert response.errors is None

        # Verify locations exist in database
        locations = db_session.query(StorageLocation).all()
        assert len(locations) == 3
        assert [loc.name for loc in locations] == ["shelfa", "shelfb", "shelfc"]

    def test_successful_grid_creation(self, db_session):
        """Test successful creation of 2D grid layout."""
        service = BulkCreateService(db_session)
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
                    range_type=RangeType.NUMBERS, start=1, end=3, zero_pad=False
                ),
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )
        # Will create: boxA-1, boxA-2, boxA-3, boxB-1, boxB-2, boxB-3

        response = service.bulk_create_locations(config)

        assert response.success is True
        assert response.created_count == 6
        assert len(response.created_ids) == 6

        # Verify locations in database
        locations = (
            db_session.query(StorageLocation).order_by(StorageLocation.name).all()
        )
        assert len(locations) == 6
        assert locations[0].name == "boxA-1"
        assert locations[-1].name == "boxB-3"

    def test_successful_3d_grid_creation(self, db_session):
        """Test successful creation of 3D grid layout."""
        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID_3D,
            prefix="rack",
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
                    range_type=RangeType.NUMBERS, start=1, end=2, zero_pad=False
                ),
            ],
            separators=["-", "-"],
            location_type="drawer",
            single_part_only=False,
        )
        # Total: 2 * 2 * 2 = 8 locations

        response = service.bulk_create_locations(config)

        assert response.success is True
        assert response.created_count == 8
        assert len(response.created_ids) == 8

        # Verify all created
        locations = db_session.query(StorageLocation).all()
        assert len(locations) == 8

    def test_layout_config_persistence(self, db_session):
        """Test layout_config is properly persisted as JSON (FR-016)."""
        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="test-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=3, zero_pad=True
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )

        response = service.bulk_create_locations(config)

        assert response.success is True

        # Verify layout_config is stored correctly
        locations = db_session.query(StorageLocation).all()
        for location in locations:
            assert location.layout_config is not None
            assert location.layout_config["layout_type"] == "row"
            assert location.layout_config["prefix"] == "test-"
            assert len(location.layout_config["ranges"]) == 1
            assert location.layout_config["ranges"][0]["zero_pad"] is True

    def test_parent_id_assignment(self, db_session):
        """Test parent_id is correctly assigned to all created locations (FR-014)."""
        # Create parent location
        parent = StorageLocation(name="parent-drawer", type="drawer")
        db_session.add(parent)
        db_session.commit()
        db_session.refresh(parent)

        service = BulkCreateService(db_session)
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

        response = service.bulk_create_locations(config)

        assert response.success is True
        assert response.created_count == 5

        # Verify all locations have correct parent_id
        child_locations = (
            db_session.query(StorageLocation)
            .filter(StorageLocation.name.like("slot-%"))
            .all()
        )
        assert len(child_locations) == 5
        for child in child_locations:
            assert child.parent_id == parent.id

    def test_location_type_assignment(self, db_session):
        """Test location type is correctly assigned (FR-021)."""
        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="drawer-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=3, zero_pad=False
                )
            ],
            separators=[],
            location_type="drawer",
            single_part_only=False,
        )

        response = service.bulk_create_locations(config)

        assert response.success is True

        # Verify location type
        locations = db_session.query(StorageLocation).all()
        for location in locations:
            assert location.type == "drawer"

    def test_auto_generated_description(self, db_session):
        """Test auto-generated description is set correctly."""
        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="test",
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
            ],
            separators=["-"],
            location_type="bin",
            single_part_only=False,
        )

        response = service.bulk_create_locations(config)

        assert response.success is True

        # Verify description
        locations = db_session.query(StorageLocation).all()
        for location in locations:
            assert "Auto-generated" in location.description
            assert "grid" in location.description.lower()

    def test_duplicate_names_validation_error(self, db_session):
        """Test creation fails with validation error for duplicate names (FR-007)."""
        # Create existing location
        existing = StorageLocation(name="bin-2", type="bin")
        db_session.add(existing)
        db_session.commit()

        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="bin-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=5, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )
        # Will try to create bin-1 through bin-5, but bin-2 exists

        response = service.bulk_create_locations(config)

        assert response.success is False
        assert response.created_count == 0
        assert len(response.created_ids) == 0
        assert response.errors is not None
        assert len(response.errors) > 0
        assert any("duplicate" in error.lower() for error in response.errors)

        # Verify NO new locations were created (all-or-nothing)
        new_locations = (
            db_session.query(StorageLocation)
            .filter(StorageLocation.name.like("bin-%"))
            .all()
        )
        assert len(new_locations) == 1  # Only the existing one

    def test_exceeds_500_limit_validation_error(self, db_session):
        """Test creation fails when exceeding 500 location limit (FR-008)."""
        service = BulkCreateService(db_session)
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

        response = service.bulk_create_locations(config)

        assert response.success is False
        assert response.created_count == 0
        assert len(response.created_ids) == 0
        assert response.errors is not None
        assert any("500" in error for error in response.errors)

        # Verify no locations were created
        locations = db_session.query(StorageLocation).all()
        assert len(locations) == 0

    def test_parent_not_found_validation_error(self, db_session):
        """Test creation fails when parent_id doesn't exist (FR-014)."""
        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="orphan-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=3, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            parent_id="00000000-0000-0000-0000-000000000000",  # Non-existent
            single_part_only=False,
        )

        response = service.bulk_create_locations(config)

        assert response.success is False
        assert response.created_count == 0
        assert len(response.created_ids) == 0
        assert response.errors is not None
        assert any("parent" in error.lower() for error in response.errors)

        # Verify no locations were created
        locations = db_session.query(StorageLocation).all()
        assert len(locations) == 0

    def test_single_layout_creation(self, db_session):
        """Test creation of SINGLE layout (just one location)."""
        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.SINGLE,
            prefix="main-room",
            ranges=[],
            separators=[],
            location_type="room",
            single_part_only=False,
        )

        response = service.bulk_create_locations(config)

        assert response.success is True
        assert response.created_count == 1
        assert len(response.created_ids) == 1

        # Verify location
        locations = db_session.query(StorageLocation).all()
        assert len(locations) == 1
        assert locations[0].name == "main-room"

    def test_large_batch_creation(self, db_session):
        """Test creation of large batch (approaching warning threshold)."""
        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.GRID,
            prefix="large",
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
        # Total: 5 * 20 = 100 locations

        response = service.bulk_create_locations(config)

        assert response.success is True
        assert response.created_count == 100
        assert len(response.created_ids) == 100

        # Verify all created
        locations = db_session.query(StorageLocation).all()
        assert len(locations) == 100


class TestTransactionSemantics:
    """Test transactional behavior and rollback scenarios."""

    def test_all_or_nothing_on_duplicate(self, db_session):
        """Test all-or-nothing: if one duplicate, none are created."""
        # Create single duplicate in the middle
        existing = StorageLocation(name="test-5", type="bin")
        db_session.add(existing)
        db_session.commit()

        service = BulkCreateService(db_session)
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
        # Tries to create test-1 through test-10, but test-5 exists

        response = service.bulk_create_locations(config)

        # Should fail completely
        assert response.success is False
        assert response.created_count == 0

        # Verify NONE of the new locations were created
        all_locations = db_session.query(StorageLocation).all()
        assert len(all_locations) == 1  # Only the original existing one
        assert all_locations[0].name == "test-5"

    def test_created_ids_match_database(self, db_session):
        """Test returned created_ids match actual database IDs."""
        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="verify-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=5, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )

        response = service.bulk_create_locations(config)

        assert response.success is True
        assert len(response.created_ids) == 5

        # Verify IDs exist in database
        for location_id in response.created_ids:
            location = (
                db_session.query(StorageLocation).filter_by(id=location_id).first()
            )
            assert location is not None
            assert location.name.startswith("verify-")

    def test_database_state_unchanged_on_error(self, db_session):
        """Test database state is unchanged when creation fails."""
        # Create some existing locations
        initial_locations = [
            StorageLocation(name="initial-1", type="bin"),
            StorageLocation(name="initial-2", type="bin"),
        ]
        db_session.add_all(initial_locations)
        db_session.commit()

        initial_count = db_session.query(StorageLocation).count()

        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="fail-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="z",
                    capitalize=False,
                )
            ],
            separators=[],
            location_type="bin",
            parent_id="00000000-0000-0000-0000-000000000000",  # Invalid parent
            single_part_only=False,
        )

        response = service.bulk_create_locations(config)

        assert response.success is False

        # Verify database unchanged
        final_count = db_session.query(StorageLocation).count()
        assert final_count == initial_count

        # Verify original locations still exist
        existing = (
            db_session.query(StorageLocation).order_by(StorageLocation.name).all()
        )
        assert len(existing) == 2
        assert existing[0].name == "initial-1"
        assert existing[1].name == "initial-2"


class TestBulkCreateEdgeCases:
    """Test edge cases and special scenarios."""

    def test_creation_with_zero_padding(self, db_session):
        """Test creation with zero-padded numbers."""
        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="pad-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=10, zero_pad=True
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )

        response = service.bulk_create_locations(config)

        assert response.success is True
        assert response.created_count == 10

        # Verify names have padding
        locations = (
            db_session.query(StorageLocation).order_by(StorageLocation.name).all()
        )
        assert locations[0].name == "pad-01"
        assert locations[9].name == "pad-10"

    def test_creation_with_capitalization(self, db_session):
        """Test creation with capitalized letters."""
        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="SHELF-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.LETTERS,
                    start="a",
                    end="e",
                    capitalize=True,
                )
            ],
            separators=[],
            location_type="shelf",
            single_part_only=False,
        )

        response = service.bulk_create_locations(config)

        assert response.success is True
        assert response.created_count == 5

        # Verify capitalization
        locations = (
            db_session.query(StorageLocation).order_by(StorageLocation.name).all()
        )
        expected_names = ["SHELF-A", "SHELF-B", "SHELF-C", "SHELF-D", "SHELF-E"]
        actual_names = [loc.name for loc in locations]
        assert actual_names == expected_names

    def test_creation_with_multiple_separators(self, db_session):
        """Test creation with different separators for 3D layout."""
        service = BulkCreateService(db_session)
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

        response = service.bulk_create_locations(config)

        assert response.success is True
        assert response.created_count == 8

        # Verify separator usage
        locations = (
            db_session.query(StorageLocation).order_by(StorageLocation.name).all()
        )
        assert locations[0].name == "locX:1.1"
        assert locations[-1].name == "locY:2.2"

    def test_user_id_parameter_optional(self, db_session):
        """Test user_id parameter is optional (for future audit trail)."""
        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="test-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=3, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )

        # Call without user_id
        response1 = service.bulk_create_locations(config)
        assert response1.success is True

        # Clear database
        db_session.query(StorageLocation).delete()
        db_session.commit()

        # Call with user_id
        response2 = service.bulk_create_locations(config, user_id="test-user-id")
        assert response2.success is True

    def test_response_schema_validation(self, db_session):
        """Test BulkCreateResponse follows schema constraints."""
        service = BulkCreateService(db_session)
        config = LayoutConfiguration(
            layout_type=LayoutType.ROW,
            prefix="schema-",
            ranges=[
                RangeSpecification(
                    range_type=RangeType.NUMBERS, start=1, end=5, zero_pad=False
                )
            ],
            separators=[],
            location_type="bin",
            single_part_only=False,
        )

        response = service.bulk_create_locations(config)

        # Verify schema constraints
        assert response.created_count == len(response.created_ids)
        assert response.success == (response.created_count > 0)
        if not response.success:
            assert response.errors is not None
        else:
            assert response.errors is None or len(response.errors) == 0
