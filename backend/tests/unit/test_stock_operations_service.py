"""
Unit tests for StockOperationsService business logic based on data-model.md
Tests service methods: add_stock, remove_stock, and move_stock operations
"""

from decimal import Decimal

import pytest
from backend.src.models import Component, ComponentLocation, StorageLocation, StockTransaction, TransactionType
from backend.src.services.stock_operations import StockOperationsService
from fastapi import HTTPException


@pytest.mark.unit
class TestStockOperationsService:
    """Unit tests for stock operations service business logic"""

    def test_add_stock_quantity_update(self, db_session):
        """
        Test add_stock: quantity updates correctly at ComponentLocation
        Verifies that adding stock increments quantity_on_hand
        """
        # Setup
        component = Component(id="test-component-1", name="Test Component")
        location = StorageLocation(id="test-location-1", name="Test Location", type="drawer")
        comp_location = ComponentLocation(
            id="test-comp-loc-1",
            component_id=component.id,
            storage_location_id=location.id,
            quantity_on_hand=50,
        )

        db_session.add_all([component, location, comp_location])
        db_session.commit()

        # Execute service method
        service = StockOperationsService(db_session)
        result = service.add_stock(
            component_id=component.id,
            location_id=location.id,
            quantity=30,
            user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
        )

        # Verify quantity update
        assert result["success"] is True
        assert result["quantity_added"] == 30
        assert result["previous_quantity"] == 50
        assert result["new_quantity"] == 80

        # Verify database state
        db_session.refresh(comp_location)
        assert comp_location.quantity_on_hand == 80

    def test_add_stock_pricing_calculation(self, db_session):
        """
        Test add_stock: pricing calculation (per-unit vs total)
        Verifies that service correctly handles both pricing modes
        """
        # Setup
        component = Component(id="test-component-2", name="Test Component")
        location = StorageLocation(id="test-location-2", name="Test Location", type="drawer")

        db_session.add_all([component, location])
        db_session.commit()

        service = StockOperationsService(db_session)
        user = {"user_id": "test-user", "user_name": "Test User", "is_admin": True}

        # Test per-unit pricing: service should calculate total_price
        result1 = service.add_stock(
            component_id=component.id,
            location_id=location.id,
            quantity=100,
            price_per_unit=Decimal("0.50"),
            user=user,
        )
        db_session.commit()

        # Verify transaction has calculated total_price
        tx1 = db_session.get(StockTransaction, result1["transaction_id"])
        assert tx1.price_per_unit == Decimal("0.50")
        assert tx1.total_price == Decimal("50.00")

        # Test total lot pricing: service should calculate price_per_unit
        result2 = service.add_stock(
            component_id=component.id,
            location_id=location.id,
            quantity=50,
            total_price=Decimal("37.50"),
            user=user,
        )
        db_session.commit()

        # Verify transaction has calculated price_per_unit
        tx2 = db_session.get(StockTransaction, result2["transaction_id"])
        assert tx2.total_price == Decimal("37.50")
        assert tx2.price_per_unit == Decimal("0.75")

    def test_add_stock_transaction_creation(self, db_session):
        """
        Test add_stock: StockTransaction audit record creation
        Verifies that service creates immutable audit trail entry
        """
        # Setup
        component = Component(id="test-component-3", name="Test Component")
        location = StorageLocation(id="test-location-3", name="Test Location", type="drawer")
        comp_location = ComponentLocation(
            id="test-comp-loc-3",
            component_id=component.id,
            storage_location_id=location.id,
            quantity_on_hand=100,
        )

        db_session.add_all([component, location, comp_location])
        db_session.commit()

        # Execute service method
        service = StockOperationsService(db_session)
        result = service.add_stock(
            component_id=component.id,
            location_id=location.id,
            quantity=25,
            user={"user_id": "user-123", "user_name": "John Doe", "is_admin": True},
            comments="Test stock addition",
        )
        db_session.commit()

        # Verify StockTransaction was created
        transaction = db_session.get(StockTransaction, result["transaction_id"])
        assert transaction is not None
        assert transaction.transaction_type == TransactionType.ADD
        assert transaction.quantity_change == 25
        assert transaction.previous_quantity == 100
        assert transaction.new_quantity == 125
        assert transaction.to_location_id == location.id
        assert transaction.from_location_id is None
        assert transaction.user_id == "user-123"
        assert transaction.user_name == "John Doe"

    def test_remove_stock_auto_capping(self, db_session):
        """
        Test remove_stock: auto-capping behavior when requested > available
        Verifies FR-017 requirement for automatic quantity capping
        """
        # Setup
        component = Component(id="test-component-4", name="Test Component")
        location = StorageLocation(id="test-location-4", name="Test Location", type="drawer")
        comp_location = ComponentLocation(
            id="test-comp-loc-4",
            component_id=component.id,
            storage_location_id=location.id,
            quantity_on_hand=30,  # Only 30 available
        )

        db_session.add_all([component, location, comp_location])
        db_session.commit()

        # Try to remove 50 (more than available)
        service = StockOperationsService(db_session)
        result = service.remove_stock(
            component_id=component.id,
            location_id=location.id,
            quantity=50,  # Requesting more than available
            user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
        )

        # Verify auto-capping
        assert result["capped"] is True
        assert result["requested_quantity"] == 50
        assert result["quantity_removed"] == 30  # Capped at available
        assert result["previous_quantity"] == 30
        assert result["new_quantity"] == 0
        assert "auto-capped" in result["message"]

        # Verify database state - location should be deleted (zero quantity cleanup)
        assert result["location_deleted"] is True
        comp_location_check = db_session.get(ComponentLocation, comp_location.id)
        assert comp_location_check is None  # Should be deleted

    def test_remove_stock_negative_quantity_prevention(self, db_session):
        """
        Test remove_stock: prevents negative quantity_on_hand
        Verifies that service never allows negative stock
        """
        # Setup
        component = Component(id="test-component-5", name="Test Component")
        location = StorageLocation(id="test-location-5", name="Test Location", type="drawer")
        comp_location = ComponentLocation(
            id="test-comp-loc-5",
            component_id=component.id,
            storage_location_id=location.id,
            quantity_on_hand=10,
        )

        db_session.add_all([component, location, comp_location])
        db_session.commit()

        # Try to remove more than available
        service = StockOperationsService(db_session)
        result = service.remove_stock(
            component_id=component.id,
            location_id=location.id,
            quantity=20,
            user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
        )

        # Verify quantity never went negative
        assert result["new_quantity"] == 0
        assert result["capped"] is True

        # Location should be deleted (zero quantity cleanup)
        assert result["location_deleted"] is True
        comp_location_check = db_session.get(ComponentLocation, comp_location.id)
        assert comp_location_check is None  # Should be deleted

    def test_remove_stock_location_cleanup_on_zero(self, db_session):
        """
        Test remove_stock: deletes ComponentLocation when quantity reaches 0
        Verifies FR-021 requirement for zero-quantity cleanup
        """
        # Setup
        component = Component(id="test-component-6", name="Test Component")
        location = StorageLocation(id="test-location-6", name="Test Location", type="drawer")
        comp_location = ComponentLocation(
            id="test-comp-loc-6",
            component_id=component.id,
            storage_location_id=location.id,
            quantity_on_hand=25,
        )

        db_session.add_all([component, location, comp_location])
        db_session.commit()
        comp_location_id = comp_location.id

        # Remove all stock
        service = StockOperationsService(db_session)
        result = service.remove_stock(
            component_id=component.id,
            location_id=location.id,
            quantity=25,
            user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
        )
        db_session.commit()

        # Verify ComponentLocation was deleted
        assert result["location_deleted"] is True
        assert result["new_quantity"] == 0

        deleted_location = db_session.get(ComponentLocation, comp_location_id)
        assert deleted_location is None

    def test_move_stock_atomicity(self, db_session):
        """
        Test move_stock: atomic transfer (both succeed or both fail)
        Verifies FR-033 requirement for atomicity
        """
        # Setup
        component = Component(id="test-component-7", name="Test Component")
        location_a = StorageLocation(id="test-loc-7a", name="Location A", type="drawer", qr_code_id="QR-7A")
        location_b = StorageLocation(id="test-loc-7b", name="Location B", type="drawer", qr_code_id="QR-7B")
        comp_loc_a = ComponentLocation(
            id="comp-loc-a",
            component_id=component.id,
            storage_location_id=location_a.id,
            quantity_on_hand=100,
        )
        comp_loc_b = ComponentLocation(
            id="comp-loc-b",
            component_id=component.id,
            storage_location_id=location_b.id,
            quantity_on_hand=50,
        )

        db_session.add_all([component, location_a, location_b, comp_loc_a, comp_loc_b])
        db_session.commit()

        # Move stock
        service = StockOperationsService(db_session)
        result = service.move_stock(
            component_id=component.id,
            source_location_id=location_a.id,
            destination_location_id=location_b.id,
            quantity=30,
            user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
        )
        db_session.commit()

        # Verify atomic update
        db_session.refresh(comp_loc_a)
        db_session.refresh(comp_loc_b)

        assert comp_loc_a.quantity_on_hand == 70  # 100 - 30
        assert comp_loc_b.quantity_on_hand == 80  # 50 + 30

        # Verify total unchanged
        assert result["total_stock"] == 150

    def test_move_stock_pricing_inheritance(self, db_session):
        """
        Test move_stock: pricing inheritance from source to destination
        Verifies FR-034 requirement for preserving pricing/lot data
        """
        # Setup
        component = Component(id="test-component-8", name="Test Component")
        location_a = StorageLocation(id="test-loc-8a", name="Location A", type="drawer", qr_code_id="QR-8A")
        location_b = StorageLocation(id="test-loc-8b", name="Location B", type="drawer", qr_code_id="QR-8B")
        comp_loc_a = ComponentLocation(
            id="comp-loc-a",
            component_id=component.id,
            storage_location_id=location_a.id,
            quantity_on_hand=100,
            unit_cost_at_location=Decimal("0.50"),  # Source has pricing
        )

        db_session.add_all([component, location_a, location_b, comp_loc_a])
        db_session.commit()

        # Move to new location (B doesn't exist yet)
        service = StockOperationsService(db_session)
        result = service.move_stock(
            component_id=component.id,
            source_location_id=location_a.id,
            destination_location_id=location_b.id,
            quantity=40,
            user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
        )
        db_session.commit()

        # Verify pricing inheritance
        assert result["pricing_inherited"] is True
        assert result["destination_location_created"] is True

        # Verify destination has inherited pricing
        comp_loc_b = (
            db_session.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component.id,
                ComponentLocation.storage_location_id == location_b.id,
            )
            .first()
        )
        assert comp_loc_b is not None
        assert comp_loc_b.unit_cost_at_location == Decimal("0.50")

    def test_move_stock_source_destination_updates(self, db_session):
        """
        Test move_stock: correct updates to both source and destination
        Verifies that both locations are updated correctly
        """
        # Setup
        component = Component(id="test-component-9", name="Test Component")
        location_a = StorageLocation(id="test-loc-9a", name="Location A", type="drawer", qr_code_id="QR-9A")
        location_b = StorageLocation(id="test-loc-9b", name="Location B", type="drawer", qr_code_id="QR-9B")
        comp_loc_a = ComponentLocation(
            id="comp-loc-a",
            component_id=component.id,
            storage_location_id=location_a.id,
            quantity_on_hand=100,
        )
        comp_loc_b = ComponentLocation(
            id="comp-loc-b",
            component_id=component.id,
            storage_location_id=location_b.id,
            quantity_on_hand=50,
        )

        db_session.add_all([component, location_a, location_b, comp_loc_a, comp_loc_b])
        db_session.commit()

        # Move 30 units from A to B
        service = StockOperationsService(db_session)
        result = service.move_stock(
            component_id=component.id,
            source_location_id=location_a.id,
            destination_location_id=location_b.id,
            quantity=30,
            user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
        )

        # Verify response data
        assert result["source_previous_quantity"] == 100
        assert result["source_new_quantity"] == 70
        assert result["destination_previous_quantity"] == 50
        assert result["destination_new_quantity"] == 80
        assert result["quantity_moved"] == 30

    def test_move_stock_total_quantity_validation(self, db_session):
        """
        Test move_stock: total component quantity unchanged after move
        Verifies FR-038 requirement that moves don't change total quantity
        """
        # Setup
        component = Component(id="test-component-10", name="Test Component")
        location_a = StorageLocation(id="test-loc10a", name="Location A", type="drawer", qr_code_id="QR-10A")
        location_b = StorageLocation(id="test-loc10b", name="Location B", type="drawer", qr_code_id="QR-10B")
        location_c = StorageLocation(id="test-loc10c", name="Location C", type="drawer", qr_code_id="QR-10C")

        comp_loc_a = ComponentLocation(
            id="comp-loc-a",
            component_id=component.id,
            storage_location_id=location_a.id,
            quantity_on_hand=100,
        )
        comp_loc_b = ComponentLocation(
            id="comp-loc-b",
            component_id=component.id,
            storage_location_id=location_b.id,
            quantity_on_hand=50,
        )
        comp_loc_c = ComponentLocation(
            id="comp-loc-c",
            component_id=component.id,
            storage_location_id=location_c.id,
            quantity_on_hand=25,
        )

        db_session.add_all([
            component, location_a, location_b, location_c,
            comp_loc_a, comp_loc_b, comp_loc_c,
        ])
        db_session.commit()

        # Total before move: 100 + 50 + 25 = 175
        total_before = component.quantity_on_hand
        assert total_before == 175

        # Move 40 from A to B
        service = StockOperationsService(db_session)
        result = service.move_stock(
            component_id=component.id,
            source_location_id=location_a.id,
            destination_location_id=location_b.id,
            quantity=40,
            user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
        )
        db_session.commit()

        # Verify total unchanged
        db_session.refresh(component)
        total_after = component.quantity_on_hand
        assert total_after == 175
        assert result["total_stock"] == 175

    def test_service_requires_user_context(self, db_session):
        """
        Test that all stock operations require user context for audit trail
        Verifies that user_id and user_name are captured in transactions
        """
        # Setup
        component = Component(id="test-component-11", name="Test Component")
        location = StorageLocation(id="test-location-11", name="Test Location", type="drawer")

        db_session.add_all([component, location])
        db_session.commit()

        # Execute add_stock with user context
        service = StockOperationsService(db_session)
        user = {"user_id": "user-456", "user_name": "Jane Smith", "is_admin": True}

        result = service.add_stock(
            component_id=component.id,
            location_id=location.id,
            quantity=10,
            user=user,
        )
        db_session.commit()

        # Verify transaction has user data
        transaction = db_session.get(StockTransaction, result["transaction_id"])
        assert transaction.user_id == "user-456"
        assert transaction.user_name == "Jane Smith"

    def test_service_validates_component_exists(self, db_session):
        """
        Test that service validates component exists before operation
        Should raise appropriate error if component not found
        """
        # Setup - create location but no component
        location = StorageLocation(id="test-location-12", name="Test Location", type="drawer")
        db_session.add(location)
        db_session.commit()

        # Try to add stock for non-existent component
        service = StockOperationsService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.add_stock(
                component_id="non-existent-component",
                location_id=location.id,
                quantity=10,
                user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
            )

        assert exc_info.value.status_code == 404
        assert "Component not found" in exc_info.value.detail

    def test_service_validates_location_exists(self, db_session):
        """
        Test that service validates storage location exists before operation
        Should raise appropriate error if location not found
        """
        # Setup - create component but no location
        component = Component(id="test-component-13", name="Test Component")
        db_session.add(component)
        db_session.commit()

        # Try to add stock at non-existent location
        service = StockOperationsService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.add_stock(
                component_id=component.id,
                location_id="non-existent-location",
                quantity=10,
                user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
            )

        assert exc_info.value.status_code == 404
        assert "Storage location not found" in exc_info.value.detail

    def test_move_stock_validates_same_location(self, db_session):
        """
        Test that move_stock rejects same source and destination
        Verifies validation of different locations
        """
        # Setup
        component = Component(id="test-component-14", name="Test Component")
        location = StorageLocation(id="test-location-14", name="Test Location", type="drawer")
        comp_location = ComponentLocation(
            id="comp-loc-14",
            component_id=component.id,
            storage_location_id=location.id,
            quantity_on_hand=100,
        )

        db_session.add_all([component, location, comp_location])
        db_session.commit()

        # Try to move to same location
        service = StockOperationsService(db_session)

        with pytest.raises(HTTPException) as exc_info:
            service.move_stock(
                component_id=component.id,
                source_location_id=location.id,
                destination_location_id=location.id,  # Same as source
                quantity=10,
                user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
            )

        assert exc_info.value.status_code == 400
        assert "must be different" in exc_info.value.detail

    def test_move_stock_source_cleanup_on_zero(self, db_session):
        """
        Test move_stock: deletes source ComponentLocation when quantity reaches 0
        Verifies FR-035 requirement for source location cleanup
        """
        # Setup
        component = Component(id="test-component-15", name="Test Component")
        location_a = StorageLocation(id="test-loc15a", name="Location A", type="drawer", qr_code_id="QR-15A")
        location_b = StorageLocation(id="test-loc15b", name="Location B", type="drawer", qr_code_id="QR-15B")
        comp_loc_a = ComponentLocation(
            id="comp-loc-a",
            component_id=component.id,
            storage_location_id=location_a.id,
            quantity_on_hand=50,
        )

        db_session.add_all([component, location_a, location_b, comp_loc_a])
        db_session.commit()
        comp_loc_a_id = comp_loc_a.id

        # Move all stock from A to B
        service = StockOperationsService(db_session)
        result = service.move_stock(
            component_id=component.id,
            source_location_id=location_a.id,
            destination_location_id=location_b.id,
            quantity=50,
            user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
        )
        db_session.commit()

        # Verify source was deleted
        assert result["source_location_deleted"] is True
        assert result["source_new_quantity"] == 0

        deleted_location = db_session.get(ComponentLocation, comp_loc_a_id)
        assert deleted_location is None

    def test_move_stock_auto_capping(self, db_session):
        """
        Test move_stock: auto-capping behavior when requested > available
        Verifies FR-029 requirement for automatic quantity capping in moves
        """
        # Setup
        component = Component(id="test-component-16", name="Test Component")
        location_a = StorageLocation(id="test-loc16a", name="Location A", type="drawer", qr_code_id="QR-16A")
        location_b = StorageLocation(id="test-loc16b", name="Location B", type="drawer", qr_code_id="QR-16B")
        comp_loc_a = ComponentLocation(
            id="comp-loc-a",
            component_id=component.id,
            storage_location_id=location_a.id,
            quantity_on_hand=20,  # Only 20 available
        )

        db_session.add_all([component, location_a, location_b, comp_loc_a])
        db_session.commit()

        # Try to move 50 (more than available)
        service = StockOperationsService(db_session)
        result = service.move_stock(
            component_id=component.id,
            source_location_id=location_a.id,
            destination_location_id=location_b.id,
            quantity=50,
            user={"user_id": "test-user", "user_name": "Test User", "is_admin": True},
        )
        db_session.commit()

        # Verify auto-capping
        assert result["capped"] is True
        assert result["requested_quantity"] == 50
        assert result["quantity_moved"] == 20  # Capped at available
        assert "auto-capped" in result["message"]
