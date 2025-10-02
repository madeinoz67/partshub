"""
ComponentLocation model for tracking component inventory across multiple storage locations.
"""

import uuid

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class ComponentLocation(Base):
    """
    Junction table that tracks component quantities across multiple storage locations.

    This allows a single component (same part number) to be stored in multiple locations
    with different quantities, enabling flexible inventory management.
    """

    __tablename__ = "component_locations"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign keys
    component_id = Column(
        String, ForeignKey("components.id"), nullable=False, index=True
    )
    storage_location_id = Column(
        String, ForeignKey("storage_locations.id"), nullable=False, index=True
    )

    # Location-specific inventory data
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    quantity_ordered = Column(Integer, nullable=False, default=0)
    minimum_stock = Column(Integer, nullable=False, default=0)

    # Location-specific notes and data
    location_notes = Column(Text, nullable=True)  # Notes specific to this location
    unit_cost_at_location = Column(
        Numeric(10, 4), nullable=True
    )  # Location-specific cost

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    component = relationship("Component", back_populates="locations")
    storage_location = relationship(
        "StorageLocation", back_populates="component_locations"
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            "component_id", "storage_location_id", name="uq_component_location"
        ),
    )

    def __repr__(self):
        return f"<ComponentLocation(component_id='{self.component_id}', location_id='{self.storage_location_id}', quantity={self.quantity_on_hand})>"

    @property
    def is_low_stock(self):
        """Check if component at this location is below minimum stock threshold."""
        return self.quantity_on_hand <= self.minimum_stock

    @property
    def is_out_of_stock(self):
        """Check if component at this location is completely out of stock."""
        return self.quantity_on_hand == 0
