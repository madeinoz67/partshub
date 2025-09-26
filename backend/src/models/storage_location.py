"""
StorageLocation model with hierarchy support for organizing components.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, event
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

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
    type = Column(String(20), nullable=False)  # container, room, building, cabinet, drawer, shelf, bin

    # Hierarchy support
    parent_id = Column(String, ForeignKey("storage_locations.id"), nullable=True)
    location_hierarchy = Column(String(500), nullable=False, index=True)  # Full path: "Workshop/Cabinet-A/Drawer-1"

    # QR code for physical identification
    qr_code_id = Column(String(50), nullable=True, unique=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    parent = relationship("StorageLocation", remote_side=[id], back_populates="children")
    children = relationship("StorageLocation", back_populates="parent", cascade="all, delete-orphan")
    components = relationship("Component", back_populates="storage_location")

    def __repr__(self):
        return f"<StorageLocation(id='{self.id}', name='{self.name}', hierarchy='{self.location_hierarchy}')>"

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
        return len(self.location_hierarchy.split("/")) - 1 if self.location_hierarchy else 0

    def get_all_descendants(self):
        """Get all descendant storage locations recursively."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def get_component_count(self, include_children=False):
        """Get count of components in this location (optionally including children)."""
        count = len(self.components)
        if include_children:
            for child in self.children:
                count += child.get_component_count(include_children=True)
        return count


# Event listener to automatically update location_hierarchy
@event.listens_for(StorageLocation.parent_id, 'set')
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

@event.listens_for(StorageLocation.name, 'set')
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