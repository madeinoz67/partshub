"""
Tag and ComponentTag junction models for flexible component labeling.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Table, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base

# Association table for many-to-many relationship between components and tags
component_tags = Table(
    'component_tags',
    Base.metadata,
    Column('component_id', String, ForeignKey('components.id'), primary_key=True),
    Column('tag_id', String, ForeignKey('tags.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now())
)


class Tag(Base):
    """
    Tag model for flexible component labeling and organization.
    """
    __tablename__ = "tags"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Display properties
    color = Column(String(7), nullable=True)  # Hex color code for UI display
    is_system_tag = Column(String, nullable=False, default=False)  # System vs user-created

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    components = relationship("Component", secondary=component_tags, back_populates="tags")

    def __repr__(self):
        return f"<Tag(id='{self.id}', name='{self.name}')>"

    @property
    def component_count(self):
        """Get count of components with this tag."""
        return len(self.components)
