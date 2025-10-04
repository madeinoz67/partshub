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
    select,
)
from sqlalchemy.orm import Session, relationship
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

    @classmethod
    def acquire_lock(cls, session: Session, location_ids: list[str]) -> list["ComponentLocation"]:
        """
        Acquire pessimistic locks on multiple component locations.

        Uses SQLAlchemy's with_for_update(nowait=False) for blocking row-level locks.
        Locations are locked in consistent order (sorted by ID) to prevent deadlocks.

        Args:
            session: SQLAlchemy session
            location_ids: List of location UUIDs to lock

        Returns:
            List of locked ComponentLocation instances (in sorted ID order)

        Raises:
            OperationalError: If lock cannot be acquired (timeout or conflict)

        Example:
            >>> locked_locations = ComponentLocation.acquire_lock(session, ["id1", "id2"])
            >>> # Perform stock operations on locked_locations
            >>> session.commit()  # Releases locks
        """
        # Handle edge case: empty list
        if not location_ids:
            return []

        # Sort location_ids to ensure consistent ordering (deadlock prevention)
        sorted_ids = sorted(location_ids)

        # Query with pessimistic locking (blocking mode)
        stmt = (
            select(cls)
            .where(cls.id.in_(sorted_ids))
            .with_for_update(nowait=False)
            .order_by(cls.id)  # Ensure consistent ordering in result
        )

        # Execute and return locked instances
        result = session.execute(stmt).scalars().all()

        return list(result)
