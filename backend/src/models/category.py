"""
Category model with tree structure for organizing component types.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..database import Base


class Category(Base):
    """
    Hierarchical category model for organizing component types
    (e.g., Passive > Resistors > Carbon Film, Active > ICs > Microcontrollers).
    """
    __tablename__ = "categories"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Tree structure
    parent_id = Column(String, ForeignKey("categories.id"), nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)  # For custom ordering within parent

    # Display properties
    color = Column(String(7), nullable=True)  # Hex color code for UI display
    icon = Column(String(50), nullable=True)  # Icon identifier for UI

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent", order_by=sort_order, cascade="all, delete-orphan")
    components = relationship("Component", back_populates="category")

    def __repr__(self):
        return f"<Category(id='{self.id}', name='{self.name}', parent_id='{self.parent_id}')>"

    @property
    def full_path(self):
        """Get the full hierarchical path as a list of Category objects."""
        path = []
        current = self
        while current:
            path.insert(0, current)
            current = current.parent
        return path

    @property
    def full_path_names(self):
        """Get the full hierarchical path as a list of category names."""
        return [cat.name for cat in self.full_path]

    @property
    def breadcrumb(self):
        """Get breadcrumb string for display (e.g., 'Passive > Resistors > Carbon Film')."""
        return " > ".join(self.full_path_names)

    @property
    def depth(self):
        """Get the depth level in the hierarchy (0 for root)."""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth

    def get_all_descendants(self):
        """Get all descendant categories recursively."""
        descendants = []
        for child in self.children:
            descendants.append(child)
            descendants.extend(child.get_all_descendants())
        return descendants

    def get_component_count(self, include_children=False):
        """Get count of components in this category (optionally including children)."""
        count = len(self.components)
        if include_children:
            for child in self.children:
                count += child.get_component_count(include_children=True)
        return count

    def is_ancestor_of(self, other_category):
        """Check if this category is an ancestor of another category."""
        if not other_category.parent:
            return False
        if other_category.parent_id == self.id:
            return True
        return self.is_ancestor_of(other_category.parent)

    def is_descendant_of(self, other_category):
        """Check if this category is a descendant of another category."""
        return other_category.is_ancestor_of(self)