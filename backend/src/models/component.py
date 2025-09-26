"""
Component model with JSON specifications field for flexible component data storage.
"""

from sqlalchemy import Column, String, Integer, Text, Numeric, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..database import Base


class Component(Base):
    """
    Central entity representing electronic parts with specifications, quantities, and relationships.

    Uses JSON fields for flexible component specifications that vary by component type
    (e.g., resistors have resistance/tolerance, microcontrollers have memory/frequency).
    """
    __tablename__ = "components"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    part_number = Column(String(100), nullable=True, index=True)
    manufacturer = Column(String(100), nullable=True, index=True)

    # Classification and location
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    storage_location_id = Column(String, ForeignKey("storage_locations.id"), nullable=True)
    component_type = Column(String(50), nullable=True, index=True)  # resistor, capacitor, IC, etc.
    value = Column(String(50), nullable=True)  # 10kΩ, 100μF, etc.
    package = Column(String(50), nullable=True)  # 0805, DIP8, SOT-23, etc.

    # Inventory quantities
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    quantity_ordered = Column(Integer, nullable=False, default=0)
    minimum_stock = Column(Integer, nullable=False, default=0)

    # Financial tracking
    average_purchase_price = Column(Numeric(10, 4), nullable=True)
    total_purchase_value = Column(Numeric(12, 2), nullable=True)

    # Flexible data storage
    notes = Column(Text, nullable=True)
    specifications = Column(JSON, nullable=True)  # Component-specific electrical/mechanical parameters
    custom_fields = Column(JSON, nullable=True)  # User-defined attributes and metadata
    provider_data = Column(JSON, nullable=True)  # Cached data from component providers (LCSC, Octopart, etc.)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="components")
    storage_location = relationship("StorageLocation", back_populates="components")
    stock_transactions = relationship("StockTransaction", back_populates="component", cascade="all, delete-orphan")
    project_components = relationship("ProjectComponent", back_populates="component", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="component_tags", back_populates="components")
    attachments = relationship("Attachment", back_populates="component", cascade="all, delete-orphan")
    custom_field_values = relationship("CustomFieldValue", back_populates="component", cascade="all, delete-orphan")
    substitute_for = relationship("Substitute", foreign_keys="Substitute.component_id", back_populates="component")
    substitute_options = relationship("Substitute", foreign_keys="Substitute.substitute_component_id", back_populates="substitute_component")
    purchase_items = relationship("PurchaseItem", back_populates="component", cascade="all, delete-orphan")
    provider_data_cache = relationship("ComponentProviderData", back_populates="component", cascade="all, delete-orphan")
    kicad_data = relationship("KiCadLibraryData", back_populates="component", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Component(id='{self.id}', name='{self.name}', part_number='{self.part_number}')>"

    @property
    def display_name(self):
        """Human-readable display name combining name and part number."""
        if self.part_number:
            return f"{self.name} ({self.part_number})"
        return self.name

    @property
    def is_low_stock(self):
        """Check if component is below minimum stock threshold."""
        return self.quantity_on_hand <= self.minimum_stock

    @property
    def is_out_of_stock(self):
        """Check if component is completely out of stock."""
        return self.quantity_on_hand == 0