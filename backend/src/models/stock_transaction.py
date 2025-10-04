"""
StockTransaction audit model for tracking all inventory changes.
"""

import enum
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class TransactionType(enum.Enum):
    """Stock transaction type enumeration."""

    ADD = "add"  # Adding stock (purchase, found, etc.)
    REMOVE = "remove"  # Removing stock (used, broken, lost, etc.)
    MOVE = "move"  # Moving between locations (no quantity change)
    ADJUST = "adjust"  # Inventory correction/adjustment


class StockTransaction(Base):
    """
    Audit trail for all component stock changes with full traceability.
    """

    __tablename__ = "stock_transactions"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    component_id = Column(String, ForeignKey("components.id"), nullable=False)

    # Transaction details
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    quantity_change = Column(Integer, nullable=False)  # Can be positive or negative
    previous_quantity = Column(Integer, nullable=False)  # Stock before transaction
    new_quantity = Column(Integer, nullable=False)  # Stock after transaction

    # Context and traceability
    reason = Column(Text, nullable=False)  # Human-readable reason
    reference_id = Column(
        String, nullable=True
    )  # Reference to related entity (purchase, project, etc.)
    reference_type = Column(
        String(50), nullable=True
    )  # Type of reference (purchase, project, adjustment, etc.)

    # Location tracking (for moves)
    from_location_id = Column(String, ForeignKey("storage_locations.id"), nullable=True)
    to_location_id = Column(String, ForeignKey("storage_locations.id"), nullable=True)

    # User tracking (when implemented)
    user_id = Column(String, nullable=True)  # Who performed the transaction
    user_name = Column(
        String(100), nullable=True
    )  # Cached username for historical reference

    # Metadata
    batch_id = Column(String, nullable=True)  # For grouping related transactions
    notes = Column(Text, nullable=True)  # Additional notes

    # Lot and pricing tracking (added in migration f3c7d9e5a2b1)
    lot_id = Column(String(100), nullable=True, index=True)  # Lot/batch identifier
    price_per_unit = Column(
        Numeric(10, 4), nullable=True
    )  # Unit price at time of transaction
    total_price = Column(
        Numeric(10, 4), nullable=True
    )  # Total transaction price (quantity * price_per_unit)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    component = relationship("Component", back_populates="stock_transactions")
    from_location = relationship("StorageLocation", foreign_keys=[from_location_id])
    to_location = relationship("StorageLocation", foreign_keys=[to_location_id])

    def __repr__(self):
        return f"<StockTransaction(id='{self.id}', component_id='{self.component_id}', type='{self.transaction_type.value}', qty_change={self.quantity_change}, lot_id='{self.lot_id}', total_price={self.total_price})>"

    @property
    def is_stock_increase(self):
        """Check if this transaction increases stock."""
        return self.quantity_change > 0

    @property
    def is_stock_decrease(self):
        """Check if this transaction decreases stock."""
        return self.quantity_change < 0

    @property
    def is_location_move(self):
        """Check if this is a location move transaction."""
        return (
            self.transaction_type == TransactionType.MOVE
            and self.from_location_id is not None
            and self.to_location_id is not None
        )

    @property
    def absolute_quantity_change(self):
        """Get absolute value of quantity change."""
        return abs(self.quantity_change)

    @property
    def display_description(self):
        """Get human-readable description of the transaction."""
        sign = "+" if self.quantity_change >= 0 else ""
        qty_str = f"{sign}{self.quantity_change}"
        base = f"{self.transaction_type.value.upper()} {qty_str}"
        if self.notes:
            return f"{base} - {self.notes}"
        return base

    @classmethod
    def create_add_transaction(
        cls, component, quantity, reason, reference_id=None, reference_type=None
    ):
        """Helper method to create an ADD transaction."""
        return cls(
            component_id=component.id,
            transaction_type=TransactionType.ADD,
            quantity_change=quantity,
            previous_quantity=component.quantity_on_hand,
            new_quantity=component.quantity_on_hand + quantity,
            reason=reason,
            reference_id=reference_id,
            reference_type=reference_type,
        )

    @classmethod
    def create_remove_transaction(
        cls, component, quantity, reason, reference_id=None, reference_type=None
    ):
        """Helper method to create a REMOVE transaction."""
        return cls(
            component_id=component.id,
            transaction_type=TransactionType.REMOVE,
            quantity_change=-quantity,
            previous_quantity=component.quantity_on_hand,
            new_quantity=component.quantity_on_hand - quantity,
            reason=reason,
            reference_id=reference_id,
            reference_type=reference_type,
        )

    @classmethod
    def create_move_transaction(
        cls, component, from_location, to_location, reason, reference_id=None
    ):
        """Helper method to create a MOVE transaction."""
        return cls(
            component_id=component.id,
            transaction_type=TransactionType.MOVE,
            quantity_change=0,  # No quantity change for moves
            previous_quantity=component.quantity_on_hand,
            new_quantity=component.quantity_on_hand,
            from_location_id=from_location.id if from_location else None,
            to_location_id=to_location.id if to_location else None,
            reason=reason,
            reference_id=reference_id,
            reference_type="location_move",
        )

    @classmethod
    def create_adjustment_transaction(
        cls, component, new_quantity, reason, reference_id=None
    ):
        """Helper method to create an ADJUST transaction."""
        quantity_change = new_quantity - component.quantity_on_hand
        return cls(
            component_id=component.id,
            transaction_type=TransactionType.ADJUST,
            quantity_change=quantity_change,
            previous_quantity=component.quantity_on_hand,
            new_quantity=new_quantity,
            reason=reason,
            reference_id=reference_id,
            reference_type="inventory_adjustment",
        )
