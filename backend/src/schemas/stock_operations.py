"""
Pydantic schemas for stock management operations.

This module defines request/response models for stock operations including:
- Add stock (receiving, manual entry)
- Remove stock (usage, damage, loss)
- Move stock (location transfers)

All operations are admin-only and support atomic transactions with full audit trails.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class AddStockRequest(BaseModel):
    """
    Request schema for adding stock to a component at a specific location.

    Admin-only operation that creates a ComponentLocation entry (or updates existing)
    and records a StockTransaction audit entry.

    Supports two pricing modes:
    - Per component: Specify price_per_unit only
    - Entire lot: Specify total_price only
    Cannot specify both pricing fields simultaneously.

    Examples:
        Manual entry with per-unit pricing:
            {
                "location_id": "660e8400-e29b-41d4-a716-446655440001",
                "quantity": 100,
                "price_per_unit": 0.50,
                "lot_id": "LOT-2025-Q1-001",
                "comments": "Manual stock addition - quarterly restock"
            }

        Receiving against purchase order:
            {
                "location_id": "660e8400-e29b-41d4-a716-446655440001",
                "quantity": 50,
                "total_price": 25.00,
                "reference_id": "PO-2025-001",
                "comments": "Received shipment against PO-2025-001"
            }
    """

    location_id: UUID = Field(
        ..., description="UUID of the storage location to add stock to"
    )
    quantity: int = Field(
        ..., ge=1, description="Quantity of stock to add (must be positive)"
    )
    price_per_unit: Annotated[Decimal, Field(ge=0)] | None = Field(
        None,
        description="Price per unit (optional, for 'Per component' pricing, max 4 decimal places)",
    )
    total_price: Annotated[Decimal, Field(ge=0)] | None = Field(
        None,
        description="Total price for entire lot (optional, for 'Entire lot' pricing, max 4 decimal places)",
    )
    lot_id: str | None = Field(
        None, max_length=100, description="Lot/batch identifier for tracking (optional)"
    )
    comments: str | None = Field(
        None, description="Additional comments/notes for this stock addition"
    )
    reference_id: str | None = Field(
        None, description="Reference to related entity (e.g., order ID, purchase ID)"
    )
    reference_type: str | None = Field(
        None,
        max_length=50,
        description='Type of reference (e.g., "purchase_order", "manual_entry")',
    )

    @model_validator(mode="after")
    def validate_pricing_consistency(self):
        """
        Validate pricing field consistency.

        Rules:
        - Cannot specify both price_per_unit and total_price
        - Either field can be omitted (pricing optional)
        """
        if self.price_per_unit is not None and self.total_price is not None:
            raise ValueError("Cannot specify both price_per_unit and total_price")

        return self


class RemoveStockRequest(BaseModel):
    """
    Request schema for removing stock from a component at a specific location.

    Admin-only operation that updates ComponentLocation quantity (or deletes if zero)
    and records a StockTransaction audit entry.

    Supports auto-capping: If requested quantity exceeds available stock,
    the system automatically caps removal at available quantity.

    Examples:
        Simple stock removal:
            {
                "location_id": "660e8400-e29b-41d4-a716-446655440001",
                "quantity": 25,
                "comments": "Used in Project Alpha assembly"
            }

        Removal with explicit reason:
            {
                "location_id": "660e8400-e29b-41d4-a716-446655440001",
                "quantity": 10,
                "reason": "damaged",
                "comments": "Damaged during handling - discarded"
            }
    """

    location_id: UUID = Field(
        ..., description="UUID of the storage location to remove stock from"
    )
    quantity: int = Field(
        ...,
        ge=1,
        description="Quantity to remove (positive, auto-capped at available stock)",
    )
    comments: str | None = Field(
        None, description="Optional comments explaining the stock removal"
    )
    reason: str | None = Field(
        None, description='Reason for removal (e.g., "used", "damaged", "lost")'
    )


class MoveStockRequest(BaseModel):
    """
    Request schema for moving stock between storage locations.

    Admin-only atomic operation that decrements source location and increments
    destination location, creating audit trail with StockTransaction.

    Supports auto-capping: If requested quantity exceeds source stock,
    the system automatically caps move at available quantity.

    Features:
    - Atomicity: Both locations updated or neither (all-or-nothing)
    - Pricing inheritance: Copies lot_id and pricing from source to destination
    - Zero cleanup: Deletes source ComponentLocation if quantity reaches 0
    - Deadlock prevention: Locks acquired in consistent order

    Examples:
        Simple stock movement:
            {
                "source_location_id": "660e8400-e29b-41d4-a716-446655440001",
                "destination_location_id": "660e8400-e29b-41d4-a716-446655440002",
                "quantity": 50,
                "comments": "Moving to primary storage"
            }

        Move all stock (will delete source location):
            {
                "source_location_id": "660e8400-e29b-41d4-a716-446655440001",
                "destination_location_id": "660e8400-e29b-41d4-a716-446655440002",
                "quantity": 100,
                "comments": "Consolidating all stock to main warehouse"
            }
    """

    source_location_id: UUID = Field(
        ..., description="UUID of source location (where stock is moved from)"
    )
    destination_location_id: UUID = Field(
        ..., description="UUID of destination location (where stock is moved to)"
    )
    quantity: int = Field(
        ...,
        ge=1,
        description="Quantity to move (positive, auto-capped at source stock)",
    )
    comments: str | None = Field(
        None, description="Optional comments explaining the stock movement"
    )

    @model_validator(mode="after")
    def validate_different_locations(self):
        """
        Validate source and destination are different.

        Rules:
        - source_location_id must differ from destination_location_id
        """
        if self.source_location_id == self.destination_location_id:
            raise ValueError("Source and destination locations must be different")

        return self


class StockHistoryEntry(BaseModel):
    """
    Stock transaction history record embedded in operation responses.

    Represents a single audit trail entry from the StockTransaction table.
    Provides complete traceability for inventory changes.
    """

    id: UUID = Field(..., description="Unique transaction ID")
    component_id: UUID = Field(..., description="Component affected by transaction")
    transaction_type: str = Field(
        ..., description='Transaction type ("add", "remove", "move", "adjust")'
    )
    quantity_change: int = Field(
        ...,
        description="Quantity change (positive for additions, negative for removals)",
    )
    from_location_id: UUID | None = Field(
        None, description="Source location ID (for moves)"
    )
    to_location_id: UUID | None = Field(
        None, description="Destination location ID (for moves/adds)"
    )
    lot_id: str | None = Field(None, description="Lot/batch identifier")
    price_per_unit: Decimal | None = Field(
        None, description="Price per unit (if applicable)"
    )
    total_price: Decimal | None = Field(
        None, description="Total price for transaction (if applicable)"
    )
    user_name: str | None = Field(
        None, description="User who performed the transaction"
    )
    comments: str | None = Field(None, description="Transaction comments/notes")
    created_at: datetime = Field(..., description="Timestamp of transaction")

    class Config:
        """Pydantic configuration."""

        from_attributes = True  # Enable ORM mode for SQLAlchemy models


class AddStockResponse(BaseModel):
    """
    Response schema for successful add stock operation.

    Provides detailed information about the stock addition including
    before/after quantities and audit trail reference.
    """

    success: bool = Field(True, description="Operation success flag")
    message: str = Field(
        ..., description='Success message (e.g., "Stock added successfully")'
    )
    transaction_id: UUID = Field(
        ..., description="ID of created StockTransaction record"
    )
    component_id: UUID = Field(..., description="Component ID")
    location_id: UUID = Field(..., description="Storage location ID")
    quantity_added: int = Field(..., description="Quantity of stock added")
    previous_quantity: int = Field(
        ..., description="Stock quantity at location before addition"
    )
    new_quantity: int = Field(
        ..., description="Stock quantity at location after addition"
    )
    total_stock: int = Field(
        ..., description="Total component stock across all locations"
    )


class RemoveStockResponse(BaseModel):
    """
    Response schema for successful remove stock operation.

    Provides detailed information about the stock removal including
    auto-capping status and location deletion flag.
    """

    success: bool = Field(True, description="Operation success flag")
    message: str = Field(
        ...,
        description='Success message (may indicate auto-capping: "Stock removed successfully (quantity auto-capped at available stock)")',
    )
    transaction_id: UUID = Field(
        ..., description="ID of created StockTransaction record"
    )
    component_id: UUID = Field(..., description="Component ID")
    location_id: UUID = Field(..., description="Storage location ID")
    quantity_removed: int = Field(
        ...,
        description="Actual quantity removed (may be less than requested if capped)",
    )
    requested_quantity: int = Field(..., description="Originally requested quantity")
    capped: bool = Field(
        ..., description="True if quantity was auto-capped due to insufficient stock"
    )
    previous_quantity: int = Field(
        ..., description="Stock quantity at location before removal"
    )
    new_quantity: int = Field(
        ..., description="Stock quantity at location after removal (0 if deleted)"
    )
    location_deleted: bool = Field(
        ..., description="True if ComponentLocation was deleted (quantity reached 0)"
    )
    total_stock: int = Field(
        ..., description="Total component stock across all locations"
    )


class MoveStockResponse(BaseModel):
    """
    Response schema for successful move stock operation.

    Provides detailed information about the stock movement including
    source/destination changes, auto-capping status, and pricing inheritance.
    """

    success: bool = Field(True, description="Operation success flag")
    message: str = Field(
        ...,
        description="Success message (may indicate auto-capping or location creation)",
    )
    transaction_id: UUID = Field(
        ..., description="ID of created StockTransaction record"
    )
    component_id: UUID = Field(..., description="Component ID")
    source_location_id: UUID = Field(..., description="Source location ID")
    destination_location_id: UUID = Field(..., description="Destination location ID")
    quantity_moved: int = Field(
        ..., description="Actual quantity moved (may be less than requested if capped)"
    )
    requested_quantity: int = Field(..., description="Originally requested quantity")
    capped: bool = Field(
        ...,
        description="True if quantity was auto-capped due to insufficient source stock",
    )
    source_previous_quantity: int = Field(
        ..., description="Stock quantity at source location before move"
    )
    source_new_quantity: int = Field(
        ..., description="Stock quantity at source location after move (0 if deleted)"
    )
    source_location_deleted: bool = Field(
        ...,
        description="True if source ComponentLocation was deleted (quantity reached 0)",
    )
    destination_previous_quantity: int = Field(
        ...,
        description="Stock quantity at destination before move (0 if newly created)",
    )
    destination_new_quantity: int = Field(
        ..., description="Stock quantity at destination location after move"
    )
    destination_location_created: bool = Field(
        ..., description="True if destination ComponentLocation was newly created"
    )
    total_stock: int = Field(
        ...,
        description="Total component stock across all locations (unchanged by move)",
    )
    pricing_inherited: bool = Field(
        ..., description="True if pricing data was copied from source to destination"
    )
