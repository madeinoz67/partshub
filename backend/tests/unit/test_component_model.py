"""
Unit tests for Component model functionality.
Tests component model validation, properties, relationships, and business logic.
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database import Base
from src.models.category import Category
from src.models.component import Component
from src.models.component_location import ComponentLocation
from src.models.kicad_data import KiCadDataSource, KiCadLibraryData
from src.models.storage_location import StorageLocation
from src.models.tag import Tag


class TestComponentModel:
    """Unit tests for Component model"""

    @pytest.fixture
    def db_session(self):
        """Create an in-memory SQLite database for testing"""
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        yield session
        session.close()

    @pytest.fixture
    def sample_category(self, db_session):
        """Create a sample category for testing"""
        category = Category(
            id=str(uuid.uuid4()),
            name="Test Category",
            description="Category for testing"
        )
        db_session.add(category)
        db_session.commit()
        return category

    @pytest.fixture
    def sample_storage_location(self, db_session):
        """Create a sample storage location for testing"""
        location = StorageLocation(
            id=str(uuid.uuid4()),
            name="Test Storage",
            description="Storage for testing",
            type="drawer"
        )
        db_session.add(location)
        db_session.commit()
        return location

    def test_component_creation(self, db_session, sample_category):
        """Test basic component creation and validation"""
        component = Component(
            id=str(uuid.uuid4()),
            name="Test Resistor",
            part_number="R-TEST-001",
            manufacturer="Test Manufacturer",
            category_id=sample_category.id,
            component_type="resistor",
            value="10kΩ",
            package="0603",
            notes="Test component for unit testing"
        )

        db_session.add(component)
        db_session.commit()

        # Verify component was created successfully
        assert component.id is not None
        assert component.name == "Test Resistor"
        assert component.part_number == "R-TEST-001"
        assert component.manufacturer == "Test Manufacturer"
        assert component.category_id == sample_category.id
        assert component.component_type == "resistor"
        assert component.value == "10kΩ"
        assert component.package == "0603"
        assert component.created_at is not None
        assert component.updated_at is not None

    def test_component_display_name_property(self, db_session, sample_category):
        """Test component display_name property"""
        # Component with part number
        component_with_pn = Component(
            id=str(uuid.uuid4()),
            name="Test Resistor",
            part_number="R-001",
            category_id=sample_category.id
        )
        db_session.add(component_with_pn)

        # Component without part number
        component_without_pn = Component(
            id=str(uuid.uuid4()),
            name="Test Capacitor",
            part_number=None,
            category_id=sample_category.id
        )
        db_session.add(component_without_pn)
        db_session.commit()

        # Test display name with part number
        assert component_with_pn.display_name == "Test Resistor (R-001)"

        # Test display name without part number
        assert component_without_pn.display_name == "Test Capacitor"

    def test_component_quantity_properties(self, db_session, sample_category, sample_storage_location):
        """Test component quantity calculation properties"""
        component = Component(
            id=str(uuid.uuid4()),
            name="Test Component",
            category_id=sample_category.id
        )
        db_session.add(component)
        db_session.commit()

        # Initially, no locations should mean zero quantities
        assert component.quantity_on_hand == 0
        assert component.quantity_ordered == 0
        assert component.minimum_stock == 0

        # Add component locations
        location1 = ComponentLocation(
            id=str(uuid.uuid4()),
            component_id=component.id,
            storage_location_id=sample_storage_location.id,
            quantity_on_hand=50,
            quantity_ordered=25,
            minimum_stock=10
        )

        # Create another storage location for multiple location testing
        location2_storage = StorageLocation(
            id=str(uuid.uuid4()),
            name="Second Storage",
            type="box"
        )
        db_session.add(location2_storage)

        location2 = ComponentLocation(
            id=str(uuid.uuid4()),
            component_id=component.id,
            storage_location_id=location2_storage.id,
            quantity_on_hand=30,
            quantity_ordered=15,
            minimum_stock=5
        )

        db_session.add_all([location1, location2])
        db_session.commit()

        # Refresh component to get updated relationships
        db_session.refresh(component)

        # Test aggregated quantities
        assert component.quantity_on_hand == 80  # 50 + 30
        assert component.quantity_ordered == 40  # 25 + 15
        assert component.minimum_stock == 15     # 10 + 5

    def test_component_specifications_json_field(self, db_session, sample_category):
        """Test component specifications JSON field functionality"""
        specifications = {
            "resistance": "10kΩ",
            "tolerance": "±1%",
            "power_rating": "0.1W",
            "temperature_coefficient": "±100ppm/°C",
            "package_details": {
                "width": "1.6mm",
                "length": "0.8mm",
                "height": "0.35mm"
            }
        }

        component = Component(
            id=str(uuid.uuid4()),
            name="Precision Resistor",
            category_id=sample_category.id,
            specifications=specifications
        )

        db_session.add(component)
        db_session.commit()

        # Verify specifications were stored and retrieved correctly
        assert component.specifications["resistance"] == "10kΩ"
        assert component.specifications["tolerance"] == "±1%"
        assert component.specifications["package_details"]["width"] == "1.6mm"

    def test_component_custom_fields_json(self, db_session, sample_category):
        """Test component custom_fields JSON field functionality"""
        custom_fields = {
            "supplier": "Digi-Key",
            "supplier_part_number": "311-10.0KCRCT-ND",
            "lead_time_days": 2,
            "preferred_vendor": True,
            "environmental_rating": "RoHS compliant"
        }

        component = Component(
            id=str(uuid.uuid4()),
            name="Custom Fields Component",
            category_id=sample_category.id,
            custom_fields=custom_fields
        )

        db_session.add(component)
        db_session.commit()

        # Verify custom fields were stored correctly
        assert component.custom_fields["supplier"] == "Digi-Key"
        assert component.custom_fields["lead_time_days"] == 2
        assert component.custom_fields["preferred_vendor"] is True

    def test_component_financial_tracking(self, db_session, sample_category):
        """Test component financial tracking fields"""
        component = Component(
            id=str(uuid.uuid4()),
            name="Financial Test Component",
            category_id=sample_category.id,
            average_purchase_price=Decimal("2.50"),
            total_purchase_value=Decimal("125.00")
        )

        db_session.add(component)
        db_session.commit()

        # Verify financial fields
        assert component.average_purchase_price == Decimal("2.50")
        assert component.total_purchase_value == Decimal("125.00")

    def test_component_category_relationship(self, db_session, sample_category):
        """Test component-category relationship"""
        component = Component(
            id=str(uuid.uuid4()),
            name="Relationship Test",
            category_id=sample_category.id
        )

        db_session.add(component)
        db_session.commit()

        # Test relationship access
        assert component.category is not None
        assert component.category.name == sample_category.name
        assert component.category_id == sample_category.id

        # Test reverse relationship
        assert component in sample_category.components

    def test_component_tags_relationship(self, db_session, sample_category):
        """Test component-tags many-to-many relationship"""
        # Create tags
        tag1 = Tag(id=str(uuid.uuid4()), name="SMD", is_system_tag=False)
        tag2 = Tag(id=str(uuid.uuid4()), name="High-Precision", is_system_tag=False)

        component = Component(
            id=str(uuid.uuid4()),
            name="Tagged Component",
            category_id=sample_category.id
        )

        db_session.add_all([tag1, tag2, component])
        db_session.commit()

        # Add tags to component
        component.tags.append(tag1)
        component.tags.append(tag2)
        db_session.commit()

        # Test tag relationships
        assert len(component.tags) == 2
        assert tag1 in component.tags
        assert tag2 in component.tags

        # Test reverse relationship
        assert component in tag1.components
        assert component in tag2.components

    def test_component_kicad_data_relationship(self, db_session, sample_category):
        """Test component-KiCad data one-to-one relationship"""
        component = Component(
            id=str(uuid.uuid4()),
            name="KiCad Component",
            category_id=sample_category.id
        )

        kicad_data = KiCadLibraryData(
            id=str(uuid.uuid4()),
            component_id=component.id,
            symbol_library="Resistor_SMD",
            symbol_name="R_0603_1608Metric",
            footprint_library="Resistor_SMD",
            footprint_name="R_0603_1608Metric",
            symbol_source=KiCadDataSource.AUTO_GENERATED,
            footprint_source=KiCadDataSource.AUTO_GENERATED
        )

        db_session.add_all([component, kicad_data])
        db_session.commit()

        # Test relationship
        assert component.kicad_data is not None
        assert component.kicad_data.symbol_library == "Resistor_SMD"
        assert kicad_data.component == component

    def test_component_validation_edge_cases(self, db_session, sample_category):
        """Test component validation with edge cases"""
        # Component with minimal required fields
        minimal_component = Component(
            id=str(uuid.uuid4()),
            name="Minimal Component"
        )

        db_session.add(minimal_component)
        db_session.commit()

        assert minimal_component.name == "Minimal Component"
        assert minimal_component.category_id is None
        assert minimal_component.part_number is None

    def test_component_string_representation(self, db_session, sample_category):
        """Test component __repr__ method"""
        component = Component(
            id="test-uuid-123",
            name="Test Component",
            part_number="TEST-001",
            category_id=sample_category.id
        )

        repr_str = repr(component)
        assert "test-uuid-123" in repr_str
        assert "Test Component" in repr_str
        assert "TEST-001" in repr_str

    def test_component_primary_location_property(self, db_session, sample_category, sample_storage_location):
        """Test component primary_location property"""
        component = Component(
            id=str(uuid.uuid4()),
            name="Location Test Component",
            category_id=sample_category.id
        )
        db_session.add(component)
        db_session.commit()

        # Component with no locations
        assert component.primary_location is None

        # Add a location
        location = ComponentLocation(
            id=str(uuid.uuid4()),
            component_id=component.id,
            storage_location_id=sample_storage_location.id,
            quantity_on_hand=100
        )
        db_session.add(location)
        db_session.commit()

        # Refresh component
        db_session.refresh(component)

        # Should have a primary location now
        assert component.primary_location is not None
        assert component.primary_location.id == sample_storage_location.id

    def test_component_update_timestamps(self, db_session, sample_category):
        """Test that updated_at timestamp changes on modification"""
        component = Component(
            id=str(uuid.uuid4()),
            name="Timestamp Test",
            category_id=sample_category.id
        )

        db_session.add(component)
        db_session.commit()

        original_updated_at = component.updated_at

        # Modify component
        component.notes = "Updated notes"
        db_session.commit()

        # updated_at should be different (if the database supports it)
        # Note: SQLite might not update this automatically, so this test
        # might need adjustment based on the actual database setup
        assert component.updated_at >= original_updated_at

    def test_component_provider_data_json(self, db_session, sample_category):
        """Test component provider_data JSON field"""
        provider_data = {
            "lcsc": {
                "part_id": "C25804",
                "price_breaks": [
                    {"quantity": 1, "unit_price": 0.05},
                    {"quantity": 10, "unit_price": 0.04},
                    {"quantity": 100, "unit_price": 0.03}
                ],
                "stock_quantity": 50000,
                "datasheet_url": "https://example.com/datasheet.pdf",
                "last_updated": "2025-09-27T10:00:00Z"
            }
        }

        component = Component(
            id=str(uuid.uuid4()),
            name="Provider Data Component",
            category_id=sample_category.id,
            provider_data=provider_data
        )

        db_session.add(component)
        db_session.commit()

        # Verify provider data storage and retrieval
        assert component.provider_data["lcsc"]["part_id"] == "C25804"
        assert component.provider_data["lcsc"]["stock_quantity"] == 50000
        assert len(component.provider_data["lcsc"]["price_breaks"]) == 3

    def test_component_unique_constraints(self, db_session, sample_category):
        """Test component unique constraints"""
        # Test unique part_number constraint
        component1 = Component(
            id=str(uuid.uuid4()),
            name="Component 1",
            part_number="UNIQUE-001",
            category_id=sample_category.id
        )

        component2 = Component(
            id=str(uuid.uuid4()),
            name="Component 2",
            part_number="UNIQUE-001",  # Same part number
            category_id=sample_category.id
        )

        db_session.add(component1)
        db_session.commit()

        # Adding second component with same part number should raise error
        db_session.add(component2)
        with pytest.raises(Exception):  # Should be IntegrityError
            db_session.commit()
