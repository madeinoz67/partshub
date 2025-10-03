"""
StorageLocation model with hierarchy support for organizing components.
"""

import uuid
from datetime import UTC

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    event,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class StorageLocation(Base):
    """
    Hierarchical storage location model supporting nested organization
    (e.g., Workshop > Cabinet A > Drawer 1 > Bin 3).
    """

    __tablename__ = "storage_locations"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    type = Column(
        String(20), nullable=False
    )  # container, room, building, cabinet, drawer, shelf, bin

    # Hierarchy support
    parent_id = Column(String, ForeignKey("storage_locations.id"), nullable=True)
    location_hierarchy = Column(
        String(500), nullable=False, index=True
    )  # Full path: "Workshop/Cabinet-A/Drawer-1"

    # QR code for physical identification
    qr_code_id = Column(String(50), nullable=True, unique=True, index=True)
    location_code = Column(
        String(20), nullable=True, index=True
    )  # Short identifier like "A1", "B2-3"

    # Layout generation metadata (for audit trail)
    layout_config = Column(
        JSON, nullable=True
    )  # JSONB in PostgreSQL, JSON text in SQLite

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_used_at = Column(
        DateTime(timezone=True), nullable=True
    )  # Only updated when components are moved in/out

    # Relationships
    parent = relationship(
        "StorageLocation", remote_side=[id], back_populates="children"
    )
    children = relationship(
        "StorageLocation", back_populates="parent", cascade="save-update, merge"
    )
    component_locations = relationship(
        "ComponentLocation",
        back_populates="storage_location",
        cascade="save-update, merge",
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "type IN ('container', 'room', 'building', 'cabinet', 'drawer', 'shelf', 'bin', 'bag')",
            name="ck_storage_location_type_valid",
        ),
    )

    def __repr__(self):
        return f"<StorageLocation(id='{self.id}', name='{self.name}', type='{self.type}', hierarchy='{self.location_hierarchy}')>"

    @property
    def display_name(self):
        """Get display name with location code if available."""
        if self.location_code:
            return f"{self.name} ({self.location_code})"
        return self.name

    @property
    def full_path(self):
        """Get the full hierarchical path as a list of StorageLocation objects."""
        path = []
        current = self
        while current:
            path.insert(0, current)
            current = current.parent
        return path

    @property
    def depth(self):
        """Get the depth level in the hierarchy (0 for root)."""
        return (
            len(self.location_hierarchy.split("/")) - 1
            if self.location_hierarchy
            else 0
        )

    def get_all_descendants(self):
        """Get all descendant storage locations recursively."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def get_component_count(self, include_children=False):
        """Get count of components in this location (optionally including children)."""
        count = len(self.component_locations)
        if include_children:
            for child in self.children:
                count += child.get_component_count(include_children=True)
        return count

    @property
    def components(self):
        """Get all components stored in this location."""
        return [location.component for location in self.component_locations]

    def get_total_quantity(self):
        """Get total quantity of all components in this location."""
        return sum(location.quantity_on_hand for location in self.component_locations)

    def can_be_deleted(self):
        """Check if this storage location can be safely deleted."""
        # Cannot delete if it has components assigned
        if self.component_locations:
            return False, "Cannot delete storage location with assigned components"

        # Cannot delete if it has child locations with components
        for child in self.children:
            can_delete, reason = child.can_be_deleted()
            if not can_delete:
                return (
                    False,
                    f"Cannot delete storage location: child '{child.name}' {reason}",
                )

        return True, "Can be safely deleted"

    def get_deletion_blockers(self):
        """Get detailed list of what prevents deletion of this location."""
        blockers = []

        # Check for assigned components
        if self.component_locations:
            component_names = [cl.component.name for cl in self.component_locations]
            blockers.append(
                f"Contains {len(component_names)} component(s): {', '.join(component_names[:3])}{'...' if len(component_names) > 3 else ''}"
            )

        # Check child locations recursively
        for child in self.children:
            child_blockers = child.get_deletion_blockers()
            if child_blockers:
                blockers.append(f"Child '{child.name}': {'; '.join(child_blockers)}")

        return blockers

    def is_ancestor_of(self, other):
        """Check if this location is an ancestor of another location."""
        if not other:
            return False

        current = other.parent
        while current:
            if current.id == self.id:
                return True
            current = current.parent
        return False


# Event listener to automatically update location_hierarchy
@event.listens_for(StorageLocation.parent_id, "set")
def update_location_hierarchy(target, value, oldvalue, initiator):
    """Automatically update location_hierarchy when parent changes."""
    if value is None:
        # Root level location
        target.location_hierarchy = target.name
    else:
        # Find parent and build hierarchy
        from sqlalchemy.orm import object_session

        session = object_session(target)
        if session:
            parent = session.get(StorageLocation, value)
            if parent:
                target.location_hierarchy = f"{parent.location_hierarchy}/{target.name}"


@event.listens_for(StorageLocation.name, "set")
def update_hierarchy_on_name_change(target, value, oldvalue, initiator):
    """Update location_hierarchy when name changes."""
    if target.parent_id is None:
        target.location_hierarchy = value
    else:
        from sqlalchemy.orm import object_session

        session = object_session(target)
        if session:
            parent = session.get(StorageLocation, target.parent_id)
            if parent:
                target.location_hierarchy = f"{parent.location_hierarchy}/{value}"


@event.listens_for(StorageLocation, "before_insert")
def generate_qr_code_id(mapper, connection, target):
    """Auto-generate QR code ID if not already set."""
    if not target.qr_code_id:
        # Ensure ID is generated first if not already set
        if not target.id:
            target.id = str(uuid.uuid4())
        # Generate a unique QR code ID using the location's UUID
        # Format: LOC-<first 8 chars of UUID>
        target.qr_code_id = f"LOC-{target.id[:8].upper()}"


@event.listens_for(StorageLocation, "before_update")
def update_updated_at(mapper, connection, target):
    """Update updated_at timestamp on every update."""
    from datetime import datetime

    target.updated_at = datetime.now(UTC)
