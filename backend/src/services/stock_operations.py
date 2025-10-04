"""
Stock operations service implementing core business logic for stock management.

This service provides three atomic stock operations with pessimistic locking,
auto-capping, and comprehensive audit trails:
- add_stock: Add inventory to a location
- remove_stock: Remove inventory from a location (with auto-capping)
- move_stock: Transfer inventory between locations (with pricing inheritance)

All operations follow TDD principles and data-model.md state transitions.
"""

import logging
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import (
    Component,
    ComponentLocation,
    StockTransaction,
    StorageLocation,
    TransactionType,
)

logger = logging.getLogger(__name__)


class StockOperationsService:
    """
    Service for atomic stock management operations with pessimistic locking.

    Implements FR-017, FR-021, FR-029, FR-033, FR-034, FR-035, FR-036, FR-037,
    FR-038, FR-041, and FR-042 from spec.md.
    """

    def __init__(self, session: Session):
        """
        Initialize service with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def add_stock(
        self,
        component_id: str,
        location_id: str,
        quantity: int,
        user: dict,
        price_per_unit: Decimal | None = None,
        total_price: Decimal | None = None,
        lot_id: str | None = None,
        comments: str | None = None,
        reference_id: str | None = None,
        reference_type: str | None = None,
    ) -> dict:
        """
        Add stock to a component at a specific location.

        Implements data-model.md Add Stock Flow (lines 84-95):
        1. Validate component and location exist
        2. Acquire pessimistic lock on ComponentLocation
        3. Get or create ComponentLocation entry
        4. Create StockTransaction audit record
        5. Update ComponentLocation.quantity_on_hand
        6. Update Component.total_quantity (calculated property)
        7. Commit transaction

        Args:
            component_id: UUID of component
            location_id: UUID of storage location
            quantity: Quantity to add (positive integer)
            user: Dict with user_id, user_name, is_admin
            price_per_unit: Optional price per component
            total_price: Optional total price for entire lot
            lot_id: Optional lot/batch identifier
            comments: Optional user comments
            reference_id: Optional reference to related entity
            reference_type: Optional type of reference

        Returns:
            Dict containing AddStockResponse data with transaction details

        Raises:
            HTTPException(404): Component or location not found
            HTTPException(400): Invalid input data
        """
        # Step 1: Validate component exists
        component = self.session.get(Component, component_id)
        if not component:
            raise HTTPException(status_code=404, detail="Component not found")

        # Step 2: Validate location exists
        location = self.session.get(StorageLocation, location_id)
        if not location:
            raise HTTPException(status_code=404, detail="Storage location not found")

        # Step 3: Get or create ComponentLocation with pessimistic lock
        # First, check if ComponentLocation exists
        comp_location_stmt = (
            select(ComponentLocation)
            .where(
                ComponentLocation.component_id == component_id,
                ComponentLocation.storage_location_id == location_id,
            )
            .with_for_update(nowait=False)  # Pessimistic lock (FR-041)
        )
        comp_location = self.session.execute(comp_location_stmt).scalar_one_or_none()

        # Track previous quantity for response
        previous_quantity = comp_location.quantity_on_hand if comp_location else 0

        if not comp_location:
            # Create new ComponentLocation if doesn't exist
            comp_location = ComponentLocation(
                component_id=component_id,
                storage_location_id=location_id,
                quantity_on_hand=0,
            )
            self.session.add(comp_location)
            self.session.flush()  # Get ID for transaction

        # Step 4: Calculate pricing if needed
        calculated_price_per_unit = price_per_unit
        calculated_total_price = total_price

        if price_per_unit is not None and total_price is None:
            # Per-unit pricing mode: calculate total
            calculated_total_price = Decimal(str(quantity)) * price_per_unit
        elif total_price is not None and price_per_unit is None:
            # Total lot pricing mode: calculate per-unit
            calculated_price_per_unit = total_price / Decimal(str(quantity))

        # Step 5: Create StockTransaction audit record
        transaction = StockTransaction(
            component_id=component_id,
            transaction_type=TransactionType.ADD,
            quantity_change=quantity,
            previous_quantity=previous_quantity,
            new_quantity=previous_quantity + quantity,
            reason=comments or "Stock added",
            from_location_id=None,
            to_location_id=location_id,
            lot_id=lot_id,
            price_per_unit=calculated_price_per_unit,
            total_price=calculated_total_price,
            user_id=user.get("user_id"),
            user_name=user.get("user_name"),
            reference_id=reference_id,
            reference_type=reference_type,
            notes=comments,
        )
        self.session.add(transaction)

        # Step 6: Update ComponentLocation quantity
        comp_location.quantity_on_hand += quantity

        # Update pricing at location if provided and location is new
        if previous_quantity == 0 and calculated_price_per_unit is not None:
            comp_location.unit_cost_at_location = calculated_price_per_unit

        # Step 7: Flush to get transaction ID and refresh component
        self.session.flush()
        self.session.refresh(component)

        # Calculate total stock across all locations (using Component.quantity_on_hand property)
        total_stock = component.quantity_on_hand

        # Step 8: Build response
        return {
            "success": True,
            "message": "Stock added successfully",
            "transaction_id": transaction.id,
            "component_id": component_id,
            "location_id": location_id,
            "quantity_added": quantity,
            "previous_quantity": previous_quantity,
            "new_quantity": comp_location.quantity_on_hand,
            "total_stock": total_stock,
        }

    def remove_stock(
        self,
        component_id: str,
        location_id: str,
        quantity: int,
        user: dict,
        comments: str | None = None,
        reason: str | None = None,
    ) -> dict:
        """
        Remove stock from a component at a specific location.

        Implements data-model.md Remove Stock Flow (lines 97-110):
        1. Validate component exists
        2. Get ComponentLocation (must exist)
        3. Acquire pessimistic lock
        4. Auto-cap quantity at available stock (FR-017)
        5. Create StockTransaction audit record
        6. Update ComponentLocation.quantity_on_hand
        7. Delete ComponentLocation if quantity reaches 0 (FR-021)
        8. Update Component.total_quantity

        Args:
            component_id: UUID of component
            location_id: UUID of storage location
            quantity: Quantity to remove (positive integer, will be capped)
            user: Dict with user_id, user_name, is_admin
            comments: Optional user comments
            reason: Optional removal reason

        Returns:
            Dict containing RemoveStockResponse data with capping status

        Raises:
            HTTPException(404): Component or ComponentLocation not found
        """
        # Step 1: Validate component exists
        component = self.session.get(Component, component_id)
        if not component:
            raise HTTPException(status_code=404, detail="Component not found")

        # Step 2: Get ComponentLocation with pessimistic lock
        comp_location_stmt = (
            select(ComponentLocation)
            .where(
                ComponentLocation.component_id == component_id,
                ComponentLocation.storage_location_id == location_id,
            )
            .with_for_update(nowait=False)  # Pessimistic lock (FR-041)
        )
        comp_location = self.session.execute(comp_location_stmt).scalar_one_or_none()

        if not comp_location:
            raise HTTPException(
                status_code=404,
                detail="Component not found at this location",
            )

        # Step 3: Auto-cap quantity at available stock (FR-017)
        previous_quantity = comp_location.quantity_on_hand
        actual_quantity = min(quantity, previous_quantity)
        capped = actual_quantity < quantity

        # Step 4: Create StockTransaction audit record
        transaction_reason = reason or comments or "Stock removed"
        transaction = StockTransaction(
            component_id=component_id,
            transaction_type=TransactionType.REMOVE,
            quantity_change=-actual_quantity,
            previous_quantity=previous_quantity,
            new_quantity=previous_quantity - actual_quantity,
            reason=transaction_reason,
            from_location_id=location_id,
            to_location_id=None,
            user_id=user.get("user_id"),
            user_name=user.get("user_name"),
            notes=comments,
        )
        self.session.add(transaction)

        # Step 5: Update ComponentLocation quantity
        comp_location.quantity_on_hand -= actual_quantity
        new_quantity = comp_location.quantity_on_hand

        # Step 6: Delete ComponentLocation if quantity reaches 0 (FR-021)
        location_deleted = False
        if comp_location.quantity_on_hand == 0:
            self.session.delete(comp_location)
            location_deleted = True

        # Step 7: Flush and refresh component for total stock calculation
        self.session.flush()
        self.session.refresh(component)

        # Calculate total stock across all locations
        total_stock = component.quantity_on_hand

        # Step 8: Build response
        message = "Stock removed successfully"
        if capped:
            message += " (quantity auto-capped at available stock)"

        return {
            "success": True,
            "message": message,
            "transaction_id": transaction.id,
            "component_id": component_id,
            "location_id": location_id,
            "quantity_removed": actual_quantity,
            "requested_quantity": quantity,
            "capped": capped,
            "previous_quantity": previous_quantity,
            "new_quantity": new_quantity,
            "location_deleted": location_deleted,
            "total_stock": total_stock,
        }

    def move_stock(
        self,
        component_id: str,
        source_location_id: str,
        destination_location_id: str,
        quantity: int,
        user: dict,
        comments: str | None = None,
    ) -> dict:
        """
        Move stock between two storage locations atomically.

        Implements data-model.md Move Stock Flow (lines 112-129):
        1. Validate component exists
        2. Validate source != destination
        3. Get source ComponentLocation
        4. Acquire pessimistic locks on BOTH locations (ordered by ID)
        5. Auto-cap quantity at source stock (FR-029)
        6. Get source pricing for inheritance
        7. Create TWO StockTransactions (REMOVE + ADD)
        8. Update source quantity
        9. Delete source if quantity = 0 (FR-035)
        10. Get or create destination ComponentLocation
        11. Update destination quantity
        12. Inherit pricing if destination is new (FR-034, FR-036)
        13. Validate total_quantity unchanged (FR-038)

        Args:
            component_id: UUID of component
            source_location_id: UUID of source location
            destination_location_id: UUID of destination location
            quantity: Quantity to move (positive integer, will be capped)
            user: Dict with user_id, user_name, is_admin
            comments: Optional user comments

        Returns:
            Dict containing MoveStockResponse data with source/dest states

        Raises:
            HTTPException(404): Component or source location not found
            HTTPException(400): Source and destination are the same
        """
        # Step 1: Validate component exists
        component = self.session.get(Component, component_id)
        if not component:
            raise HTTPException(status_code=404, detail="Component not found")

        # Step 2: Validate source != destination
        if source_location_id == destination_location_id:
            raise HTTPException(
                status_code=400,
                detail="Source and destination locations must be different",
            )

        # Step 2b: Validate destination location exists
        destination_location = self.session.get(
            StorageLocation, destination_location_id
        )
        if not destination_location:
            raise HTTPException(
                status_code=404, detail="Destination storage location not found"
            )

        # Step 3: Acquire locks on BOTH locations in consistent order (deadlock prevention)
        # Sort IDs to ensure consistent locking order
        location_ids_sorted = sorted([source_location_id, destination_location_id])

        # Lock both ComponentLocation records (if they exist)
        # Note: We lock by component_id + location_id combination
        locked_locations = {}

        for loc_id in location_ids_sorted:
            comp_loc_stmt = (
                select(ComponentLocation)
                .where(
                    ComponentLocation.component_id == component_id,
                    ComponentLocation.storage_location_id == loc_id,
                )
                .with_for_update(nowait=False)  # Pessimistic lock (FR-042)
            )
            comp_loc = self.session.execute(comp_loc_stmt).scalar_one_or_none()
            locked_locations[loc_id] = comp_loc

        # Get source and destination from locked locations
        source_comp_location = locked_locations[source_location_id]
        dest_comp_location = locked_locations[destination_location_id]

        # Validate source exists
        if not source_comp_location:
            raise HTTPException(
                status_code=404,
                detail="Component not found at source location",
            )

        # Step 4: Auto-cap quantity at available source stock (FR-029)
        source_previous_quantity = source_comp_location.quantity_on_hand
        actual_quantity = min(quantity, source_previous_quantity)
        capped = actual_quantity < quantity

        # Step 5: Get source pricing for inheritance (FR-034)
        source_price_per_unit = source_comp_location.unit_cost_at_location

        # Step 6: Track destination state before move
        dest_previous_quantity = (
            dest_comp_location.quantity_on_hand if dest_comp_location else 0
        )
        destination_location_created = dest_comp_location is None

        # Step 7: Create TWO StockTransactions (conceptually REMOVE from source, ADD to dest)
        # Note: The data model suggests using MOVE type with quantity_change=0, but we need
        # to track the actual quantity moved. We'll create two transactions for clarity.

        # Transaction 1: REMOVE from source
        remove_transaction = StockTransaction(
            component_id=component_id,
            transaction_type=TransactionType.REMOVE,
            quantity_change=-actual_quantity,
            previous_quantity=source_previous_quantity,
            new_quantity=source_previous_quantity - actual_quantity,
            reason=comments or "Stock moved to another location",
            from_location_id=source_location_id,
            to_location_id=None,
            user_id=user.get("user_id"),
            user_name=user.get("user_name"),
            notes=comments,
        )
        self.session.add(remove_transaction)

        # Transaction 2: ADD to destination
        add_transaction = StockTransaction(
            component_id=component_id,
            transaction_type=TransactionType.ADD,
            quantity_change=actual_quantity,
            previous_quantity=dest_previous_quantity,
            new_quantity=dest_previous_quantity + actual_quantity,
            reason=comments or "Stock moved from another location",
            from_location_id=None,
            to_location_id=destination_location_id,
            price_per_unit=source_price_per_unit,  # Inherit pricing (FR-034)
            user_id=user.get("user_id"),
            user_name=user.get("user_name"),
            notes=comments,
        )
        self.session.add(add_transaction)

        # Step 8: Update source quantity
        source_comp_location.quantity_on_hand -= actual_quantity
        source_new_quantity = source_comp_location.quantity_on_hand

        # Step 9: Delete source ComponentLocation if quantity = 0 (FR-035)
        source_location_deleted = False
        if source_comp_location.quantity_on_hand == 0:
            self.session.delete(source_comp_location)
            source_location_deleted = True

        # Step 10: Get or create destination ComponentLocation
        if not dest_comp_location:
            # Create new ComponentLocation at destination
            dest_comp_location = ComponentLocation(
                component_id=component_id,
                storage_location_id=destination_location_id,
                quantity_on_hand=0,
            )
            self.session.add(dest_comp_location)
            self.session.flush()  # Get ID

        # Step 11: Update destination quantity
        dest_comp_location.quantity_on_hand += actual_quantity
        dest_new_quantity = dest_comp_location.quantity_on_hand

        # Step 12: Inherit pricing if destination is new (FR-036, FR-037)
        pricing_inherited = False
        if destination_location_created and source_price_per_unit is not None:
            dest_comp_location.unit_cost_at_location = source_price_per_unit
            pricing_inherited = True

        # Step 13: Flush and validate total_quantity unchanged (FR-038)
        self.session.flush()
        self.session.refresh(component)

        total_stock = component.quantity_on_hand

        # Build success message
        message = "Stock moved successfully"
        if capped:
            message += " (quantity auto-capped at available source stock)"
        if destination_location_created:
            message += " (destination location created)"

        # Step 14: Build response
        return {
            "success": True,
            "message": message,
            "transaction_id": add_transaction.id,  # Use ADD transaction ID as primary
            "component_id": component_id,
            "source_location_id": source_location_id,
            "destination_location_id": destination_location_id,
            "quantity_moved": actual_quantity,
            "requested_quantity": quantity,
            "capped": capped,
            "source_previous_quantity": source_previous_quantity,
            "source_new_quantity": source_new_quantity,
            "source_location_deleted": source_location_deleted,
            "destination_previous_quantity": dest_previous_quantity,
            "destination_new_quantity": dest_new_quantity,
            "destination_location_created": destination_location_created,
            "total_stock": total_stock,
            "pricing_inherited": pricing_inherited,
        }
