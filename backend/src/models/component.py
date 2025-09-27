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

    # Multiple identification fields for different purposes
    local_part_id = Column(String(50), nullable=True, unique=True, index=True)  # User-friendly local identifier (CAP-001, RES-047)
    barcode_id = Column(String(50), nullable=True, unique=True, index=True)  # Auto-generated for QR/barcode scanning
    manufacturer_part_number = Column(String(100), nullable=True, index=True)  # Official manufacturer part number
    provider_sku = Column(String(100), nullable=True, index=True)  # Provider-specific SKU (LCSC, Mouser, etc.)

    # Legacy field - maintained for backward compatibility, maps to manufacturer_part_number
    part_number = Column(String(100), nullable=True, index=True, unique=True)
    manufacturer = Column(String(100), nullable=True, index=True)

    # Classification (location now handled via ComponentLocation relationship)
    category_id = Column(String, ForeignKey("categories.id"), nullable=True)
    component_type = Column(String(50), nullable=True, index=True)  # resistor, capacitor, IC, etc.
    value = Column(String(50), nullable=True)  # 10kΩ, 100μF, etc.
    package = Column(String(50), nullable=True)  # 0805, DIP8, SOT-23, etc.

    # Inventory quantities (aggregated from all locations)
    # Note: These will be calculated properties from ComponentLocation records

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
    locations = relationship("ComponentLocation", back_populates="component", cascade="all, delete-orphan")
    stock_transactions = relationship("StockTransaction", back_populates="component", cascade="all, delete-orphan")
    project_components = relationship("ProjectComponent", back_populates="component", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="component_tags", back_populates="components")
    attachments = relationship("Attachment", back_populates="component", cascade="all, delete-orphan")
    custom_field_values = relationship("CustomFieldValue", back_populates="component", cascade="all, delete-orphan")
    substitute_for = relationship("Substitute", foreign_keys="Substitute.component_id", back_populates="component")
    substitute_options = relationship("Substitute", foreign_keys="Substitute.substitute_component_id", back_populates="substitute_component")
    purchase_items = relationship("PurchaseItem", back_populates="component", cascade="all, delete-orphan")
    provider_data_cache = relationship("ComponentProviderData", back_populates="component", cascade="all, delete-orphan")
    kicad_data = relationship("KiCadLibraryData", back_populates="component", uselist=False, cascade="all, delete-orphan", lazy="select")

    def __repr__(self):
        return f"<Component(id='{self.id}', name='{self.name}', part_number='{self.part_number}')>"

    @property
    def display_name(self):
        """Human-readable display name combining name and part number."""
        if self.part_number:
            return f"{self.name} ({self.part_number})"
        return self.name

    @property
    def quantity_on_hand(self):
        """Calculate total quantity across all storage locations."""
        return sum(location.quantity_on_hand for location in self.locations)

    @property
    def quantity_ordered(self):
        """Calculate total ordered quantity across all storage locations."""
        return sum(location.quantity_ordered for location in self.locations)

    @property
    def minimum_stock(self):
        """Calculate total minimum stock across all storage locations."""
        return sum(location.minimum_stock for location in self.locations)

    @property
    def primary_location(self):
        """Get the storage location with the highest quantity (primary location)."""
        if not self.locations:
            return None
        return max(self.locations, key=lambda loc: loc.quantity_on_hand).storage_location

    @property
    def storage_locations(self):
        """Get all storage locations where this component is stored."""
        return [location.storage_location for location in self.locations]

    @property
    def is_low_stock(self):
        """Check if component is below minimum stock threshold (any location)."""
        return any(location.is_low_stock for location in self.locations)

    @property
    def is_out_of_stock(self):
        """Check if component is completely out of stock (all locations)."""
        return self.quantity_on_hand == 0

    @property
    def effective_part_number(self):
        """Get the effective part number (manufacturer_part_number or legacy part_number)."""
        return self.manufacturer_part_number or self.part_number

    @property
    def primary_identifier(self):
        """Get the primary identifier for display (local_part_id or name)."""
        return self.local_part_id or self.name

    @property
    def scannable_id(self):
        """Get the scannable identifier (barcode_id or fallback to other IDs)."""
        return self.barcode_id or self.local_part_id or self.id

    def generate_barcode_id(self):
        """Generate a unique barcode ID similar to PartsBox format."""
        import secrets
        import string
        # Generate 26-character alphanumeric string (lowercase)
        chars = string.ascii_lowercase + string.digits
        return ''.join(secrets.choice(chars) for _ in range(26))

    def generate_local_part_id(self, prefix=None):
        """Generate a local part ID based on component type and sequence."""
        if prefix is None:
            # Generate prefix from component type
            type_prefixes = {
                'resistor': 'RES',
                'capacitor': 'CAP',
                'inductor': 'IND',
                'ic': 'IC',
                'microcontroller': 'MCU',
                'diode': 'D',
                'transistor': 'Q',
                'connector': 'CONN',
                'crystal': 'XTAL'
            }
            prefix = type_prefixes.get(self.component_type.lower() if self.component_type else '', 'PART')

        # This would need to be implemented with sequence logic from the database
        # For now, return a placeholder that should be handled by the service layer
        return f"{prefix}-{self.id[:8].upper()}"