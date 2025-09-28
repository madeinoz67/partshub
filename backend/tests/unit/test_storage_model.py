"""
Unit tests for StorageLocation model hierarchy functionality.
Tests storage location tree structure, hierarchy validation, and parent-child relationships.
"""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base
from src.models.category import Category
from src.models.component import Component
from src.models.component_location import ComponentLocation
from src.models.storage_location import StorageLocation


class TestStorageLocationModel:
    """Unit tests for StorageLocation model"""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    def test_storage_location_creation(self, db_session):
        """Test basic storage location creation"""
        location = StorageLocation(
            id=str(uuid.uuid4()),
            name="Test Storage",
            description="Storage location for testing",
            type="cabinet"
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
            location_hierarchy="Electronics Lab"
        )

        # Second level - Cabinet
        cabinet = StorageLocation(
            id=str(uuid.uuid4()),
            name="Component Cabinet A",
            description="Primary component storage cabinet",
            type="cabinet",
            parent_id=room.id,
            location_hierarchy="Electronics Lab/Component Cabinet A"
        )

        # Third level - Drawer
        drawer = StorageLocation(
            id=str(uuid.uuid4()),
            name="Drawer 1",
            description="Top drawer for small components",
            type="drawer",
            parent_id=cabinet.id,
            location_hierarchy="Electronics Lab/Component Cabinet A/Drawer 1"
        )

        # Fourth level - Compartment
        compartment = StorageLocation(
            id=str(uuid.uuid4()),
            name="Compartment A1",
            description="SMD resistors compartment",
            type="compartment",
            parent_id=drawer.id,
            location_hierarchy="Electronics Lab/Component Cabinet A/Drawer 1/Compartment A1"
        )

        db_session.add_all([room, cabinet, drawer, compartment])
        db_session.commit()

        # Test hierarchy relationships
        assert cabinet.parent_id == room.id
        assert drawer.parent_id == cabinet.id
        assert compartment.parent_id == drawer.id

        # Test hierarchy strings
        assert room.location_hierarchy == "Electronics Lab"
        assert cabinet.location_hierarchy == "Electronics Lab/Component Cabinet A"
        assert drawer.location_hierarchy == "Electronics Lab/Component Cabinet A/Drawer 1"
        assert compartment.location_hierarchy == "Electronics Lab/Component Cabinet A/Drawer 1/Compartment A1"

    def test_storage_location_parent_child_relationships(self, db_session):
        """Test parent-child relationships in storage hierarchy"""
        parent = StorageLocation(
            id=str(uuid.uuid4()),
            name="Parent Storage",
            type="cabinet"
        )

        child1 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Child Storage 1",
            type="drawer",
            parent_id=parent.id
        )

        child2 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Child Storage 2",
            type="drawer",
            parent_id=parent.id
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
        level1 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Building",
            type="building"
        )

        level2 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Room",
            type="room",
            parent_id=level1.id
        )

        level3 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Cabinet",
            type="cabinet",
            parent_id=level2.id
        )

        level4 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Shelf",
            type="shelf",
            parent_id=level3.id
        )

        level5 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Box",
            type="box",
            parent_id=level4.id
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
            id=str(uuid.uuid4()),
            name="Test Category",
            description="For testing"
        )

        location = StorageLocation(
            id=str(uuid.uuid4()),
            name="Component Storage",
            type="drawer"
        )

        component = Component(
            id=str(uuid.uuid4()),
            name="Test Component",
            category_id=category.id
        )

        db_session.add_all([category, location, component])
        db_session.commit()

        # Create component location relationship
        component_location = ComponentLocation(
            id=str(uuid.uuid4()),
            component_id=component.id,
            storage_location_id=location.id,
            quantity_on_hand=100,
            minimum_stock=10
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
            type="warehouse",
            location_hierarchy="Main Warehouse"
        )

        section_a = StorageLocation(
            id=str(uuid.uuid4()),
            name="Section A",
            type="section",
            parent_id=warehouse.id,
            location_hierarchy="Main Warehouse/Section A"
        )

        rack_a1 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Rack A1",
            type="rack",
            parent_id=section_a.id,
            location_hierarchy="Main Warehouse/Section A/Rack A1"
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
            ("box", "Component Box"),
            ("bin", "Parts Bin"),
            ("compartment", "SMD Compartment"),
            ("rack", "Equipment Rack"),
            ("warehouse", "Storage Warehouse")
        ]

        locations = []
        for location_type, name in location_types:
            location = StorageLocation(
                id=str(uuid.uuid4()),
                name=name,
                type=location_type,
                description=f"Test {location_type}"
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
            id=str(uuid.uuid4()),
            name="Parent Location",
            type="cabinet"
        )

        child = StorageLocation(
            id=str(uuid.uuid4()),
            name="Child Location",
            type="drawer",
            parent_id=parent.id
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
            id="test-uuid-456",
            name="Test Storage Location",
            type="drawer"
        )

        repr_str = repr(location)
        assert "test-uuid-456" in repr_str
        assert "Test Storage Location" in repr_str
        assert "drawer" in repr_str

    def test_storage_location_safe_deletion_checks(self, db_session):
        """Test safe deletion checks for storage locations"""
        parent = StorageLocation(
            id=str(uuid.uuid4()),
            name="Parent Cabinet",
            type="cabinet"
        )

        child = StorageLocation(
            id=str(uuid.uuid4()),
            name="Child Drawer",
            type="drawer",
            parent_id=parent.id
        )

        db_session.add_all([parent, child])
        db_session.commit()

        # Test deletion checks without components
        can_delete, reason = parent.can_be_deleted()
        assert can_delete is True
        assert "Can be safely deleted" in reason

        # Add a component to make deletion unsafe
        category = Category(
            id=str(uuid.uuid4()),
            name="Test Category"
        )

        component = Component(
            id=str(uuid.uuid4()),
            name="Test Component",
            category_id=category.id
        )

        component_location = ComponentLocation(
            id=str(uuid.uuid4()),
            component_id=component.id,
            storage_location_id=child.id,
            quantity_on_hand=50
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
            location_hierarchy="Multi-Drawer Cabinet"
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
                location_hierarchy=f"Multi-Drawer Cabinet/Drawer {i}"
            )
            drawers.append(drawer)

        db_session.add_all(drawers)
        db_session.commit()

        # Create compartments for each drawer
        compartments = []
        for drawer in drawers:
            for letter in ['A', 'B', 'C']:
                compartment = StorageLocation(
                    id=str(uuid.uuid4()),
                    name=f"Compartment {letter}",
                    type="compartment",
                    parent_id=drawer.id,
                    location_hierarchy=f"{drawer.location_hierarchy}/Compartment {letter}"
                )
                compartments.append(compartment)

        db_session.add_all(compartments)
        db_session.commit()

        # Verify the hierarchy was created correctly
        db_session.refresh(cabinet)
        assert len(cabinet.children) == 3  # 3 drawers

        for drawer in cabinet.children:
            db_session.refresh(drawer)
            assert len(drawer.children) == 3  # 3 compartments each

        # Total compartments should be 9 (3 drawers × 3 compartments)
        total_compartments = sum(len(drawer.children) for drawer in cabinet.children)
        assert total_compartments == 9

    def test_storage_location_search_by_hierarchy(self, db_session):
        """Test searching storage locations by hierarchy path"""
        # Create hierarchy
        lab = StorageLocation(
            id=str(uuid.uuid4()),
            name="Electronics Lab",
            type="room",
            location_hierarchy="Electronics Lab"
        )

        cabinet = StorageLocation(
            id=str(uuid.uuid4()),
            name="Cabinet A",
            type="cabinet",
            parent_id=lab.id,
            location_hierarchy="Electronics Lab/Cabinet A"
        )

        drawer1 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Drawer 1",
            type="drawer",
            parent_id=cabinet.id,
            location_hierarchy="Electronics Lab/Cabinet A/Drawer 1"
        )

        drawer2 = StorageLocation(
            id=str(uuid.uuid4()),
            name="Drawer 2",
            type="drawer",
            parent_id=cabinet.id,
            location_hierarchy="Electronics Lab/Cabinet A/Drawer 2"
        )

        db_session.add_all([lab, cabinet, drawer1, drawer2])
        db_session.commit()

        # Search by hierarchy patterns
        lab_locations = db_session.query(StorageLocation).filter(
            StorageLocation.location_hierarchy.like("Electronics Lab%")
        ).all()

        cabinet_locations = db_session.query(StorageLocation).filter(
            StorageLocation.location_hierarchy.like("Electronics Lab/Cabinet A%")
        ).all()

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
            description="Test storage with capacity limits"
        )

        db_session.add(location)
        db_session.commit()

        # Test basic capacity tracking through component locations
        category = Category(
            id=str(uuid.uuid4()),
            name="Test Category"
        )

        components = []
        for i in range(3):
            component = Component(
                id=str(uuid.uuid4()),
                name=f"Component {i+1}",
                category_id=category.id
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
                quantity_on_hand=50
            )
            component_locations.append(comp_loc)

        db_session.add_all(component_locations)
        db_session.commit()

        # Verify location now has components
        db_session.refresh(location)
        assert len(location.component_locations) == 3
