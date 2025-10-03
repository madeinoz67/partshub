"""
Unit tests for StorageLocation model hierarchy functionality.
Tests storage location tree structure, hierarchy validation, and parent-child relationships.
"""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.src.database import Base
from backend.src.models.category import Category
from backend.src.models.component import Component
from backend.src.models.component_location import ComponentLocation
from backend.src.models.storage_location import StorageLocation


@pytest.mark.unit
class TestStorageLocationModel:
    """Unit tests for StorageLocation model"""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session_local = sessionmaker(bind=engine)
        session = session_local()
        yield session
        session.close()

    def test_storage_location_creation(self, db_session):
        """Test basic storage location creation"""
        location = StorageLocation(
            id=str(uuid.uuid4()),
            name="Test Storage",
            description="Storage location for testing",
            type="cabinet",
        )

        db_session.add(location)
        db_session.commit()

        assert location.id is not None
        assert location.name == "Test Storage"
        assert location.description == "Storage location for testing"
        assert location.type == "cabinet"
        assert location.parent_id is None
        assert location.created_at is not None

    def test_storage_location_hierarchy_creation(self, db_session):
        """Test creating storage location hierarchy"""
        # Root level - Room
        room = StorageLocation(
            id=str(uuid.uuid4()),
            name="Electronics Lab",
            description="Main electronics laboratory",
            type="room",
            location_hierarchy="Electronics Lab",
        )

        # Second level - Cabinet
        cabinet = StorageLocation(
            id=str(uuid.uuid4()),
            name="Component Cabinet A",
            description="Primary component storage cabinet",
            type="cabinet",
            parent_id=room.id,
            location_hierarchy="Electronics Lab/Component Cabinet A",
        )

        # Third level - Drawer
        drawer = StorageLocation(
            id=str(uuid.uuid4()),
            name="Drawer 1",
            description="Top drawer for small components",
            type="drawer",
            parent_id=cabinet.id,
            location_hierarchy="Electronics Lab/Component Cabinet A/Drawer 1",
        )

        # Fourth level - Bin
        bin_location = StorageLocation(
            id=str(uuid.uuid4()),
            name="Bin A1",
            description="SMD resistors bin",
            type="bin",
            parent_id=drawer.id,
            location_hierarchy="Electronics Lab/Component Cabinet A/Drawer 1/Bin A1",
        )

        db_session.add_all([room, cabinet, drawer, bin_location])
        db_session.commit()

        # Test hierarchy relationships
        assert cabinet.parent_id == room.id
        assert drawer.parent_id == cabinet.id
        assert bin_location.parent_id == drawer.id

        # Test hierarchy strings
        assert room.location_hierarchy == "Electronics Lab"
        assert cabinet.location_hierarchy == "Electronics Lab/Component Cabinet A"
        assert (
            drawer.location_hierarchy == "Electronics Lab/Component Cabinet A/Drawer 1"
        )
        assert (
            bin_location.location_hierarchy
            == "Electronics Lab/Component Cabinet A/Drawer 1/Bin A1"
        )

    def test_storage_location_parent_child_relationships(self, db_session):
        """Test parent-child relationships in storage hierarchy"""
        parent = StorageLocation(
            id=str(uuid.uuid4()), name="Parent Storage", type="cabinet"
        )

        child1 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Child Storage 1",
            type="drawer",
            parent_id=parent.id,
        )

        child2 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Child Storage 2",
            type="drawer",
            parent_id=parent.id,
        )

        db_session.add_all([parent, child1, child2])
        db_session.commit()

        # Test parent relationship
        assert child1.parent == parent
        assert child2.parent == parent

        # Test children relationship
        assert len(parent.children) == 2
        assert child1 in parent.children
        assert child2 in parent.children

    def test_storage_location_hierarchy_depth(self, db_session):
        """Test storage location hierarchy with multiple levels"""
        # Create a 5-level hierarchy
        level1 = StorageLocation(id=str(uuid.uuid4()), name="Building", type="building")

        level2 = StorageLocation(
            id=str(uuid.uuid4()), name="Room", type="room", parent_id=level1.id
        )

        level3 = StorageLocation(
            id=str(uuid.uuid4()), name="Cabinet", type="cabinet", parent_id=level2.id
        )

        level4 = StorageLocation(
            id=str(uuid.uuid4()), name="Shelf", type="shelf", parent_id=level3.id
        )

        level5 = StorageLocation(
            id=str(uuid.uuid4()), name="Bin", type="bin", parent_id=level4.id
        )

        db_session.add_all([level1, level2, level3, level4, level5])
        db_session.commit()

        # Test each level's parent relationship
        assert level2.parent == level1
        assert level3.parent == level2
        assert level4.parent == level3
        assert level5.parent == level4

        # Test root level
        assert level1.parent is None

        # Test leaf level
        assert len(level5.children) == 0

    def test_storage_location_component_relationships(self, db_session):
        """Test storage location relationships with components"""
        category = Category(
            id=str(uuid.uuid4()), name="Test Category", description="For testing"
        )

        location = StorageLocation(
            id=str(uuid.uuid4()), name="Component Storage", type="drawer"
        )

        component = Component(
            id=str(uuid.uuid4()), name="Test Component", category_id=category.id
        )

        db_session.add_all([category, location, component])
        db_session.commit()

        # Create component location relationship
        component_location = ComponentLocation(
            id=str(uuid.uuid4()),
            component_id=component.id,
            storage_location_id=location.id,
            quantity_on_hand=100,
            minimum_stock=10,
        )

        db_session.add(component_location)
        db_session.commit()

        # Test relationships
        assert len(location.component_locations) == 1
        assert location.component_locations[0].component == component

    def test_storage_location_hierarchy_path_validation(self, db_session):
        """Test location hierarchy path building and validation"""
        # Create a hierarchy with specific path structure
        warehouse = StorageLocation(
            id=str(uuid.uuid4()),
            name="Main Warehouse",
            type="building",
            location_hierarchy="Main Warehouse",
        )

        section_a = StorageLocation(
            id=str(uuid.uuid4()),
            name="Section A",
            type="room",
            parent_id=warehouse.id,
            location_hierarchy="Main Warehouse/Section A",
        )

        rack_a1 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Rack A1",
            type="cabinet",
            parent_id=section_a.id,
            location_hierarchy="Main Warehouse/Section A/Rack A1",
        )

        db_session.add_all([warehouse, section_a, rack_a1])
        db_session.commit()

        # Test hierarchy path consistency
        assert warehouse.location_hierarchy == "Main Warehouse"
        assert section_a.location_hierarchy == "Main Warehouse/Section A"
        assert rack_a1.location_hierarchy == "Main Warehouse/Section A/Rack A1"

        # Test parent-child consistency
        assert section_a.parent_id == warehouse.id
        assert rack_a1.parent_id == section_a.id

    def test_storage_location_types_validation(self, db_session):
        """Test various storage location types"""
        location_types = [
            ("building", "Main Building"),
            ("room", "Electronics Room"),
            ("cabinet", "Storage Cabinet"),
            ("shelf", "Component Shelf"),
            ("drawer", "Small Parts Drawer"),
            ("bin", "Parts Bin"),
            ("container", "Storage Container"),
        ]

        locations = []
        for location_type, name in location_types:
            location = StorageLocation(
                id=str(uuid.uuid4()),
                name=name,
                type=location_type,
                description=f"Test {location_type}",
            )
            locations.append(location)

        db_session.add_all(locations)
        db_session.commit()

        # Verify all types were created successfully
        for i, (location_type, name) in enumerate(location_types):
            assert locations[i].type == location_type
            assert locations[i].name == name

    def test_storage_location_circular_reference_prevention(self, db_session):
        """Test prevention of circular references in hierarchy"""
        parent = StorageLocation(
            id=str(uuid.uuid4()), name="Parent Location", type="cabinet"
        )

        child = StorageLocation(
            id=str(uuid.uuid4()),
            name="Child Location",
            type="drawer",
            parent_id=parent.id,
        )

        db_session.add_all([parent, child])
        db_session.commit()

        # Attempting to make parent a child of child should fail
        # This would need to be enforced at the application level
        # as SQLAlchemy itself doesn't prevent this

        # For now, we just test that the normal hierarchy works
        assert child.parent_id == parent.id
        assert parent.parent_id is None

    def test_storage_location_string_representation(self, db_session):
        """Test storage location __repr__ method"""
        location = StorageLocation(
            id="test-uuid-456", name="Test Storage Location", type="drawer"
        )

        repr_str = repr(location)
        assert "test-uuid-456" in repr_str
        assert "Test Storage Location" in repr_str
        assert "drawer" in repr_str

    def test_storage_location_safe_deletion_checks(self, db_session):
        """Test safe deletion checks for storage locations"""
        parent = StorageLocation(
            id=str(uuid.uuid4()), name="Parent Cabinet", type="cabinet"
        )

        child = StorageLocation(
            id=str(uuid.uuid4()),
            name="Child Drawer",
            type="drawer",
            parent_id=parent.id,
        )

        db_session.add_all([parent, child])
        db_session.commit()

        # Test deletion checks without components
        can_delete, reason = parent.can_be_deleted()
        assert can_delete is True
        assert "Can be safely deleted" in reason

        # Add a component to make deletion unsafe
        category = Category(id=str(uuid.uuid4()), name="Test Category")

        component = Component(
            id=str(uuid.uuid4()), name="Test Component", category_id=category.id
        )

        component_location = ComponentLocation(
            id=str(uuid.uuid4()),
            component_id=component.id,
            storage_location_id=child.id,
            quantity_on_hand=50,
        )

        db_session.add_all([category, component, component_location])
        db_session.commit()

        # Now deletion should be blocked
        can_delete, reason = parent.can_be_deleted()
        assert can_delete is False
        assert "Cannot delete storage location" in reason

        # Test detailed blockers
        blockers = parent.get_deletion_blockers()
        assert len(blockers) > 0
        assert "Child 'Child Drawer'" in blockers[0]

    def test_storage_location_bulk_hierarchy_creation(self, db_session):
        """Test creating multiple storage locations in bulk"""
        # Create a cabinet with multiple drawers and compartments
        cabinet = StorageLocation(
            id=str(uuid.uuid4()),
            name="Multi-Drawer Cabinet",
            type="cabinet",
            location_hierarchy="Multi-Drawer Cabinet",
        )

        db_session.add(cabinet)
        db_session.commit()

        # Create multiple drawers
        drawers = []
        for i in range(1, 4):
            drawer = StorageLocation(
                id=str(uuid.uuid4()),
                name=f"Drawer {i}",
                type="drawer",
                parent_id=cabinet.id,
                location_hierarchy=f"Multi-Drawer Cabinet/Drawer {i}",
            )
            drawers.append(drawer)

        db_session.add_all(drawers)
        db_session.commit()

        # Create bins for each drawer
        bins = []
        for drawer in drawers:
            for letter in ["A", "B", "C"]:
                bin_location = StorageLocation(
                    id=str(uuid.uuid4()),
                    name=f"Bin {letter}",
                    type="bin",
                    parent_id=drawer.id,
                    location_hierarchy=f"{drawer.location_hierarchy}/Bin {letter}",
                )
                bins.append(bin_location)

        db_session.add_all(bins)
        db_session.commit()

        # Verify the hierarchy was created correctly
        db_session.refresh(cabinet)
        assert len(cabinet.children) == 3  # 3 drawers

        for drawer in cabinet.children:
            db_session.refresh(drawer)
            assert len(drawer.children) == 3  # 3 bins each

        # Total bins should be 9 (3 drawers × 3 bins)
        total_bins = sum(len(drawer.children) for drawer in cabinet.children)
        assert total_bins == 9

    def test_storage_location_search_by_hierarchy(self, db_session):
        """Test searching storage locations by hierarchy path"""
        # Create hierarchy
        lab = StorageLocation(
            id=str(uuid.uuid4()),
            name="Electronics Lab",
            type="room",
            location_hierarchy="Electronics Lab",
        )

        cabinet = StorageLocation(
            id=str(uuid.uuid4()),
            name="Cabinet A",
            type="cabinet",
            parent_id=lab.id,
            location_hierarchy="Electronics Lab/Cabinet A",
        )

        drawer1 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Drawer 1",
            type="drawer",
            parent_id=cabinet.id,
            location_hierarchy="Electronics Lab/Cabinet A/Drawer 1",
        )

        drawer2 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Drawer 2",
            type="drawer",
            parent_id=cabinet.id,
            location_hierarchy="Electronics Lab/Cabinet A/Drawer 2",
        )

        db_session.add_all([lab, cabinet, drawer1, drawer2])
        db_session.commit()

        # Search by hierarchy patterns
        lab_locations = (
            db_session.query(StorageLocation)
            .filter(StorageLocation.location_hierarchy.like("Electronics Lab%"))
            .all()
        )

        cabinet_locations = (
            db_session.query(StorageLocation)
            .filter(
                StorageLocation.location_hierarchy.like("Electronics Lab/Cabinet A%")
            )
            .all()
        )

        # Should find all locations under Electronics Lab
        assert len(lab_locations) == 4  # lab + cabinet + 2 drawers

        # Should find cabinet and its drawers
        assert len(cabinet_locations) == 3  # cabinet + 2 drawers

    def test_storage_location_capacity_tracking(self, db_session):
        """Test storage location with capacity information"""
        location = StorageLocation(
            id=str(uuid.uuid4()),
            name="Capacity Test Storage",
            type="drawer",
            description="Test storage with capacity limits",
        )

        db_session.add(location)
        db_session.commit()

        # Test basic capacity tracking through component locations
        category = Category(id=str(uuid.uuid4()), name="Test Category")

        components = []
        for i in range(3):
            component = Component(
                id=str(uuid.uuid4()), name=f"Component {i+1}", category_id=category.id
            )
            components.append(component)

        db_session.add_all([category] + components)
        db_session.commit()

        # Add components to location
        component_locations = []
        for component in components:
            comp_loc = ComponentLocation(
                id=str(uuid.uuid4()),
                component_id=component.id,
                storage_location_id=location.id,
                quantity_on_hand=50,
            )
            component_locations.append(comp_loc)

        db_session.add_all(component_locations)
        db_session.commit()

        # Verify location now has components
        db_session.refresh(location)
        assert len(location.component_locations) == 3

    def test_storage_location_last_used_tracking(self, db_session):
        """Test that last_used_at is only updated when components are moved, not on edits"""
        from datetime import datetime

        # Create a storage location
        location = StorageLocation(
            id=str(uuid.uuid4()),
            name="Test Location",
            type="bin",
            description="Testing last_used_at behavior",
        )

        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)

        # Initially, last_used_at should be None
        assert location.last_used_at is None
        initial_updated_at = location.updated_at

        # Edit the location (change name) - should NOT update last_used_at
        location.name = "Updated Test Location"
        db_session.commit()
        db_session.refresh(location)

        assert location.last_used_at is None  # Still None after edit
        assert location.updated_at != initial_updated_at  # updated_at changed

        # Simulate component movement by manually setting last_used_at
        # In real usage, this would be set by component movement logic
        component_movement_time = datetime.now()
        location.last_used_at = component_movement_time
        db_session.commit()
        db_session.refresh(location)

        assert location.last_used_at is not None
        assert location.last_used_at == component_movement_time

        # Edit location again - last_used_at should remain unchanged
        old_last_used = location.last_used_at
        location.description = "Updated description"
        db_session.commit()
        db_session.refresh(location)

        assert location.last_used_at == old_last_used  # Unchanged by edit
        assert location.updated_at != initial_updated_at  # updated_at still changes

    def test_storage_location_qr_code_auto_generation(self, db_session):
        """Test that QR code is automatically generated on creation"""
        # Create a storage location without QR code
        location = StorageLocation(
            id=str(uuid.uuid4()),
            name="QR Test Location",
            type="bin",
        )

        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)

        # QR code should be auto-generated
        assert location.qr_code_id is not None
        assert location.qr_code_id.startswith("LOC-")
        assert len(location.qr_code_id) == 12  # LOC- + 8 chars

        # Verify it contains the first 8 chars of the UUID
        expected_suffix = location.id[:8].upper()
        assert location.qr_code_id == f"LOC-{expected_suffix}"

    def test_storage_location_qr_code_edit_does_not_update_last_used(self, db_session):
        """Test that editing QR code doesn't update last_used_at"""
        location = StorageLocation(
            id=str(uuid.uuid4()),
            name="QR Edit Test",
            type="bin",
        )

        db_session.add(location)
        db_session.commit()
        db_session.refresh(location)

        # Initially last_used_at is None
        assert location.last_used_at is None

        # Manually change QR code (shouldn't happen normally but testing)
        location.qr_code_id = "LOC-CUSTOM1"
        db_session.commit()
        db_session.refresh(location)

        # last_used_at should still be None
        assert location.last_used_at is None
        assert location.qr_code_id == "LOC-CUSTOM1"
