"""
Substitute model for alternative components.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..database import Base


class Substitute(Base):
    """
    Model for tracking substitute/alternative components.
    """
    __tablename__ = "substitutes"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    component_id = Column(String, ForeignKey("components.id"), nullable=False)
    substitute_component_id = Column(String, ForeignKey("components.id"), nullable=False)

    # Relationship details
    notes = Column(Text, nullable=True)  # Notes about the substitution
    compatibility_rating = Column(String(20), nullable=True)  # perfect, good, acceptable, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    component = relationship("Component", foreign_keys=[component_id], back_populates="substitute_for")
    substitute_component = relationship("Component", foreign_keys=[substitute_component_id], back_populates="substitute_options")

    def __repr__(self):
        return f"<Substitute(component_id='{self.component_id}', substitute_id='{self.substitute_component_id}')>"