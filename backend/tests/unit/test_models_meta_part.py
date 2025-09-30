"""
Unit tests for MetaPart and MetaPartComponent models.
Tests all methods, properties, and assembly management functionality.
"""

import pytest
from unittest.mock import Mock
from src.models.meta_part import MetaPart, MetaPartComponent


class TestMetaPart:
    """Test MetaPart model methods and properties."""

    def test_init_creates_valid_instance(self):
        """Test MetaPart creation with basic fields."""
        meta_part = MetaPart(
            name="Power Supply Board",
            description="Main power supply for the system",
            version="v2.1",
            assembly_type="PCB",
            reference_designator="PCB1",
            notes="Test notes"
        )

        assert meta_part.name == "Power Supply Board"
        assert meta_part.description == "Main power supply for the system"
        assert meta_part.version == "v2.1"
        assert meta_part.assembly_type == "PCB"
        assert meta_part.reference_designator == "PCB1"
        assert meta_part.notes == "Test notes"

    def test_display_name_with_version(self):
        """Test display_name property includes version when available."""
        meta_part = MetaPart(
            name="Test Assembly",
            version="v1.0"
        )

        assert meta_part.display_name == "Test Assembly v1.0"

    def test_display_name_without_version(self):
        """Test display_name property returns name only when no version."""
        meta_part = MetaPart(name="Test Assembly")

        assert meta_part.display_name == "Test Assembly"

    def test_total_component_count_empty(self):
        """Test total_component_count returns 0 for empty assembly."""
        meta_part = MetaPart(name="Empty Assembly")
        meta_part.components = []

        assert meta_part.total_component_count == 0

    def test_total_component_count_with_components(self):
        """Test total_component_count sums all component quantities."""
        meta_part = MetaPart(name="Test Assembly")

        # Create simple objects instead of Mock to avoid SQLAlchemy issues
        class MockComponent:
            def __init__(self, qty):
                self.quantity_required = qty

        comp1 = MockComponent(5)
        comp2 = MockComponent(3)
        comp3 = MockComponent(10)

        # Can't directly assign to components due to SQLAlchemy, test the calculation
        # by temporarily overriding the property method
        original_components = meta_part.components
        meta_part.components = [comp1, comp2, comp3]

        assert meta_part.total_component_count == 18  # 5 + 3 + 10

    def test_unique_component_count_empty(self):
        """Test unique_component_count returns 0 for empty assembly."""
        meta_part = MetaPart(name="Empty Assembly")
        meta_part.components = []

        assert meta_part.unique_component_count == 0

    def test_unique_component_count_with_components(self):
        """Test unique_component_count returns number of component types."""
        meta_part = MetaPart(name="Test Assembly")
        meta_part.components = [Mock(), Mock(), Mock()]

        assert meta_part.unique_component_count == 3

    def test_calculate_total_cost_empty(self):
        """Test calculate_total_cost returns 0.0 for empty assembly."""
        meta_part = MetaPart(name="Empty Assembly")
        meta_part.components = []

        assert meta_part.calculate_total_cost() == 0.0

    def test_calculate_total_cost_with_pricing(self):
        """Test calculate_total_cost calculates correctly with component pricing."""
        meta_part = MetaPart(name="Test Assembly")

        # Mock components with pricing
        comp1 = Mock()
        comp1.quantity_required = 2
        comp1.component = Mock()
        comp1.component.average_purchase_price = 10.50

        comp2 = Mock()
        comp2.quantity_required = 3
        comp2.component = Mock()
        comp2.component.average_purchase_price = 5.25

        meta_part.components = [comp1, comp2]

        expected_cost = (2 * 10.50) + (3 * 5.25)  # 21.00 + 15.75 = 36.75
        assert meta_part.calculate_total_cost() == expected_cost

    def test_calculate_total_cost_no_pricing(self):
        """Test calculate_total_cost handles components without pricing."""
        meta_part = MetaPart(name="Test Assembly")

        # Mock components without pricing
        comp1 = Mock()
        comp1.quantity_required = 2
        comp1.component = Mock()
        comp1.component.average_purchase_price = None

        comp2 = Mock()
        comp2.quantity_required = 3
        comp2.component = None

        meta_part.components = [comp1, comp2]

        assert meta_part.calculate_total_cost() == 0.0

    def test_check_availability_empty_assembly(self):
        """Test check_availability for empty assembly."""
        meta_part = MetaPart(name="Empty Assembly")
        meta_part.components = []

        availability = meta_part.check_availability()

        assert availability["can_build"] is True
        assert availability["max_quantity"] == 0
        assert availability["missing_components"] == []
        assert availability["low_stock_components"] == []

    def test_check_availability_sufficient_stock(self):
        """Test check_availability when all components have sufficient stock."""
        meta_part = MetaPart(name="Test Assembly")

        # Mock components with sufficient stock
        comp1 = Mock()
        comp1.quantity_required = 2
        comp1.component = Mock()
        comp1.component.name = "Resistor"
        comp1.component.quantity_on_hand = 10
        comp1.component.is_low_stock = False

        comp2 = Mock()
        comp2.quantity_required = 3
        comp2.component = Mock()
        comp2.component.name = "Capacitor"
        comp2.component.quantity_on_hand = 15
        comp2.component.is_low_stock = False

        meta_part.components = [comp1, comp2]

        availability = meta_part.check_availability()

        assert availability["can_build"] is True
        assert availability["max_quantity"] == 5  # min(10//2, 15//3) = min(5, 5)
        assert availability["missing_components"] == []
        assert availability["low_stock_components"] == []

    def test_check_availability_insufficient_stock(self):
        """Test check_availability when components have insufficient stock."""
        meta_part = MetaPart(name="Test Assembly")

        # Mock component with insufficient stock
        comp1 = Mock()
        comp1.quantity_required = 10
        comp1.component = Mock()
        comp1.component.name = "Resistor"
        comp1.component.quantity_on_hand = 5

        meta_part.components = [comp1]

        availability = meta_part.check_availability()

        assert availability["can_build"] is False
        assert availability["max_quantity"] == 0
        assert len(availability["missing_components"]) == 1

        missing = availability["missing_components"][0]
        assert missing["component_name"] == "Resistor"
        assert missing["required"] == 10
        assert missing["available"] == 5
        assert missing["shortage"] == 5

    def test_check_availability_missing_component(self):
        """Test check_availability when component doesn't exist."""
        meta_part = MetaPart(name="Test Assembly")

        # Mock component reference without actual component
        comp1 = Mock()
        comp1.component_id = "nonexistent-component"
        comp1.component = None

        meta_part.components = [comp1]

        availability = meta_part.check_availability()

        assert availability["can_build"] is False
        assert availability["max_quantity"] == 0
        assert len(availability["missing_components"]) == 1

        missing = availability["missing_components"][0]
        assert "not found" in missing["component_name"]

    def test_check_availability_low_stock_warning(self):
        """Test check_availability identifies low stock components."""
        meta_part = MetaPart(name="Test Assembly")

        # Mock component with low stock
        comp1 = Mock()
        comp1.quantity_required = 2
        comp1.component = Mock()
        comp1.component.name = "Low Stock Resistor"
        comp1.component.quantity_on_hand = 10
        comp1.component.is_low_stock = True
        comp1.component.minimum_stock = 8

        meta_part.components = [comp1]

        availability = meta_part.check_availability()

        assert availability["can_build"] is True
        assert availability["max_quantity"] == 5  # 10 // 2
        assert len(availability["low_stock_components"]) == 1

        low_stock = availability["low_stock_components"][0]
        assert low_stock["component_name"] == "Low Stock Resistor"
        assert low_stock["current_stock"] == 10
        assert low_stock["minimum_stock"] == 8

    def test_repr_method(self):
        """Test __repr__ method returns expected format."""
        meta_part = MetaPart(name="Test Assembly", version="v1.0")

        repr_str = repr(meta_part)
        assert "name='Test Assembly'" in repr_str
        assert "version='v1.0'" in repr_str


class TestMetaPartComponent:
    """Test MetaPartComponent model methods and properties."""

    def test_init_creates_valid_instance(self):
        """Test MetaPartComponent creation with basic fields."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456",
            quantity_required=5,
            assembly_notes="Handle with care",
            reference_designators="R1,R2,R3"
        )

        assert meta_comp.meta_part_id == "meta-part-123"
        assert meta_comp.component_id == "component-456"
        assert meta_comp.quantity_required == 5
        assert meta_comp.assembly_notes == "Handle with care"
        assert meta_comp.reference_designators == "R1,R2,R3"

    def test_default_quantity_required(self):
        """Test quantity_required defaults to 1."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456"
        )

        assert meta_comp.quantity_required == 1

    def test_component_cost_with_pricing(self):
        """Test component_cost calculates correctly with pricing."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456",
            quantity_required=3
        )

        # Mock component with pricing
        meta_comp.component = Mock()
        meta_comp.component.average_purchase_price = 12.50

        expected_cost = 3 * 12.50  # 37.50
        assert meta_comp.component_cost == expected_cost

    def test_component_cost_no_component(self):
        """Test component_cost returns 0.0 when no component."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456",
            quantity_required=3
        )
        meta_comp.component = None

        assert meta_comp.component_cost == 0.0

    def test_component_cost_no_pricing(self):
        """Test component_cost returns 0.0 when no pricing."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456",
            quantity_required=3
        )

        # Mock component without pricing
        meta_comp.component = Mock()
        meta_comp.component.average_purchase_price = None

        assert meta_comp.component_cost == 0.0

    def test_is_available_sufficient_stock(self):
        """Test is_available returns True when sufficient stock."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456",
            quantity_required=5
        )

        # Mock component with sufficient stock
        meta_comp.component = Mock()
        meta_comp.component.quantity_on_hand = 10

        assert meta_comp.is_available is True

    def test_is_available_insufficient_stock(self):
        """Test is_available returns False when insufficient stock."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456",
            quantity_required=10
        )

        # Mock component with insufficient stock
        meta_comp.component = Mock()
        meta_comp.component.quantity_on_hand = 5

        assert meta_comp.is_available is False

    def test_is_available_no_component(self):
        """Test is_available returns False when no component."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456",
            quantity_required=5
        )
        meta_comp.component = None

        assert meta_comp.is_available is False

    def test_available_assemblies_sufficient_stock(self):
        """Test available_assemblies calculates correctly."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456",
            quantity_required=3
        )

        # Mock component with stock
        meta_comp.component = Mock()
        meta_comp.component.quantity_on_hand = 10

        assert meta_comp.available_assemblies == 3  # 10 // 3

    def test_available_assemblies_no_component(self):
        """Test available_assemblies returns 0 when no component."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456",
            quantity_required=3
        )
        meta_comp.component = None

        assert meta_comp.available_assemblies == 0

    def test_available_assemblies_zero_required(self):
        """Test available_assemblies returns 0 when quantity_required is 0."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456",
            quantity_required=0
        )

        # Mock component with stock
        meta_comp.component = Mock()
        meta_comp.component.quantity_on_hand = 10

        assert meta_comp.available_assemblies == 0

    def test_available_assemblies_insufficient_stock(self):
        """Test available_assemblies with insufficient stock."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456",
            quantity_required=5
        )

        # Mock component with insufficient stock
        meta_comp.component = Mock()
        meta_comp.component.quantity_on_hand = 3

        assert meta_comp.available_assemblies == 0  # 3 // 5

    def test_repr_method(self):
        """Test __repr__ method returns expected format."""
        meta_comp = MetaPartComponent(
            meta_part_id="meta-part-123",
            component_id="component-456",
            quantity_required=5
        )

        repr_str = repr(meta_comp)
        assert "meta_part_id='meta-part-123'" in repr_str
        assert "component_id='component-456'" in repr_str
        assert "qty=5" in repr_str