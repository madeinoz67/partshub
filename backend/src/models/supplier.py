"""
Supplier model for vendor information and purchasing history.
"""

from sqlalchemy import Column, String, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..database import Base


class Supplier(Base):
    """
    Vendor information and purchasing history.

    Manages supplier data for component purchasing including contact information,
    website details, and notes. Links to Purchase records for historical tracking.
    """
    __tablename__ = "suppliers"

    # Primary identifier
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Core supplier information
    name = Column(String(255), nullable=False, unique=True)
    website = Column(String(500), nullable=True)
    contact_email = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    purchases = relationship("Purchase", back_populates="supplier", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('name', name='uq_supplier_name'),
    )

    def __repr__(self):
        return f"<Supplier(id='{self.id}', name='{self.name}')>"

    @property
    def display_name(self) -> str:
        """Return the supplier name for display purposes."""
        return self.name

    def to_dict(self) -> dict:
        """Convert supplier to dictionary for API responses."""
        return {
            'id': self.id,
            'name': self.name,
            'website': self.website,
            'contact_email': self.contact_email,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }