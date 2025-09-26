"""
Purchase and PurchaseItem models for component acquisition history and pricing.
"""

from sqlalchemy import Column, String, Text, DateTime, Date, Numeric, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from decimal import Decimal

from ..database import Base


class Purchase(Base):
    """
    Component acquisition history and pricing.

    Tracks purchase records from suppliers including total costs, order references,
    and purchase dates. Links to PurchaseItems for individual component details.
    """
    __tablename__ = "purchases"

    # Primary identifier
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key relationships
    supplier_id = Column(String, ForeignKey('suppliers.id'), nullable=False)

    # Purchase information
    purchase_date = Column(Date, nullable=False)
    total_cost = Column(Numeric(precision=10, scale=2), nullable=False, default=0.00)
    currency = Column(String(3), nullable=False, default='USD')
    order_reference = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    supplier = relationship("Supplier", back_populates="purchases")
    purchase_items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Purchase(id='{self.id}', supplier='{self.supplier_id}', date='{self.purchase_date}')>"

    @property
    def total_cost_decimal(self) -> Decimal:
        """Return total cost as Decimal for precise calculations."""
        return Decimal(str(self.total_cost)) if self.total_cost else Decimal('0.00')

    @property
    def item_count(self) -> int:
        """Return the number of items in this purchase."""
        return len(self.purchase_items) if self.purchase_items else 0

    def to_dict(self, include_items: bool = False) -> dict:
        """Convert purchase to dictionary for API responses."""
        result = {
            'id': self.id,
            'supplier_id': self.supplier_id,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'total_cost': str(self.total_cost_decimal),
            'currency': self.currency,
            'order_reference': self.order_reference,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'item_count': self.item_count,
        }

        if include_items and self.purchase_items:
            result['items'] = [item.to_dict() for item in self.purchase_items]

        return result


class PurchaseItem(Base):
    """
    Individual component items within a purchase.

    Tracks specific components purchased including quantities and unit prices.
    Links to Purchase and Component for detailed purchase tracking.
    """
    __tablename__ = "purchase_items"

    # Primary identifier
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key relationships
    purchase_id = Column(String, ForeignKey('purchases.id'), nullable=False)
    component_id = Column(String, ForeignKey('components.id'), nullable=False)

    # Item details
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(precision=10, scale=4), nullable=False)
    supplier_part_number = Column(String(255), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    purchase = relationship("Purchase", back_populates="purchase_items")
    component = relationship("Component", back_populates="purchase_items")

    def __repr__(self):
        return f"<PurchaseItem(id='{self.id}', component='{self.component_id}', qty={self.quantity})>"

    @property
    def unit_price_decimal(self) -> Decimal:
        """Return unit price as Decimal for precise calculations."""
        return Decimal(str(self.unit_price)) if self.unit_price else Decimal('0.0000')

    @property
    def total_price(self) -> Decimal:
        """Calculate total price for this line item (quantity * unit_price)."""
        return self.unit_price_decimal * Decimal(str(self.quantity))

    def to_dict(self, include_component: bool = False) -> dict:
        """Convert purchase item to dictionary for API responses."""
        result = {
            'id': self.id,
            'purchase_id': self.purchase_id,
            'component_id': self.component_id,
            'quantity': self.quantity,
            'unit_price': str(self.unit_price_decimal),
            'total_price': str(self.total_price),
            'supplier_part_number': self.supplier_part_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_component and self.component:
            result['component'] = {
                'id': self.component.id,
                'name': self.component.name,
                'part_number': self.component.part_number,
                'manufacturer': self.component.manufacturer,
            }

        return result