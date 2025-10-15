"""
SavedSearch model for storing user's component search queries.
"""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class SavedSearch(Base):
    """
    SavedSearch model for saving and reusing component search queries.

    Allows users to save complex search criteria including filters,
    search text, and sorting preferences for quick reuse.
    """

    __tablename__ = "saved_searches"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Search metadata
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)

    # Search parameters stored as JSON
    # Example: {
    #   "search": "resistor",
    #   "category": "passive",
    #   "component_type": "resistor",
    #   "stock_status": "available",
    #   "tags": ["surface-mount"],
    #   "sort_by": "name",
    #   "sort_order": "asc"
    # }
    search_parameters = Column(JSON, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", backref="saved_searches")

    def __repr__(self):
        return f"<SavedSearch(id='{self.id}', name='{self.name}', user_id='{self.user_id}')>"

    def mark_as_used(self):
        """Update the last_used_at timestamp."""
        from datetime import UTC, datetime

        self.last_used_at = datetime.now(UTC)
