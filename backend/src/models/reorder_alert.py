"""
ReorderAlert model for tracking stock reorder notifications.

Alerts are automatically created and managed by database triggers when
component stock levels fall below configured thresholds.
"""

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..database import Base


class ReorderAlert(Base):
    """
    Alert generated when component stock falls below reorder threshold.

    Alerts are automatically created by database triggers and follow a
    workflow: active → dismissed/ordered → resolved.

    Attributes:
        id: Auto-incrementing primary key
        component_location_id: Foreign key to component_locations
        component_id: Denormalized foreign key to components (for query efficiency)
        storage_location_id: Denormalized foreign key to storage_locations
        status: Current alert state (active, dismissed, ordered, resolved)
        current_quantity: Stock quantity when alert was last updated
        reorder_threshold: The threshold that triggered this alert
        shortage_amount: Calculated shortage (threshold - current_quantity)
        created_at: When alert was first created
        updated_at: When alert was last modified
        dismissed_at: When alert was dismissed (if applicable)
        ordered_at: When alert was marked as ordered (if applicable)
        resolved_at: When alert was auto-resolved by restocking
        notes: Optional user notes (e.g., PO number, dismissal reason)

    Relationships:
        component_location: The ComponentLocation that triggered this alert
        component: The Component (denormalized for convenience)
        storage_location: The StorageLocation (denormalized for convenience)

    Workflow:
        1. Trigger creates alert with status='active' when stock drops below threshold
        2. User can dismiss (status='dismissed') or mark as ordered (status='ordered')
        3. Trigger auto-resolves (status='resolved') when stock rises above threshold
    """

    __tablename__ = "reorder_alerts"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    component_location_id = Column(
        Integer, ForeignKey("component_locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    component_id = Column(
        String, ForeignKey("components.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    storage_location_id = Column(
        String, ForeignKey("storage_locations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Alert state
    status = Column(String, nullable=False, default="active", index=True)

    # Stock information
    current_quantity = Column(Integer, nullable=False)
    reorder_threshold = Column(Integer, nullable=False)
    shortage_amount = Column(Integer, nullable=False)

    # Timestamps (managed by database triggers)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
    dismissed_at = Column(String, nullable=True)
    ordered_at = Column(String, nullable=True)
    resolved_at = Column(String, nullable=True)

    # User notes
    notes = Column(String, nullable=True)

    # Relationships
    component_location = relationship(
        "ComponentLocation",
        back_populates="reorder_alerts"
    )
    component = relationship("Component")
    storage_location = relationship("StorageLocation")

    def __repr__(self):
        return (
            f"<ReorderAlert(id={self.id}, "
            f"component_id='{self.component_id}', "
            f"status='{self.status}', "
            f"shortage={self.shortage_amount})>"
        )

    @property
    def is_active(self) -> bool:
        """Check if alert requires attention."""
        return self.status == "active"

    @property
    def is_resolved(self) -> bool:
        """Check if alert has been resolved."""
        return self.status == "resolved"

    @property
    def shortage_percentage(self) -> float:
        """Calculate shortage as percentage of reorder threshold."""
        if self.reorder_threshold == 0:
            return 0.0
        return (self.shortage_amount / self.reorder_threshold) * 100

    @property
    def severity(self) -> str:
        """
        Calculate alert severity based on shortage percentage.

        Returns:
            'critical' if shortage > 80% of threshold
            'high' if shortage > 50% of threshold
            'medium' if shortage > 20% of threshold
            'low' otherwise
        """
        pct = self.shortage_percentage
        if pct > 80:
            return "critical"
        elif pct > 50:
            return "high"
        elif pct > 20:
            return "medium"
        else:
            return "low"
