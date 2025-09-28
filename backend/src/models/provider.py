"""
ComponentDataProvider model for external service configuration.
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class ComponentDataProvider(Base):
    """
    External service configuration for component data providers.

    Manages configuration for external providers (LCSC, Octopart, Mouser, DigiKey)
    that can provide component specifications, datasheets, and images.
    """
    __tablename__ = "component_data_providers"

    # Primary identifier
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Provider configuration
    name = Column(String(255), nullable=False, unique=True)
    api_url = Column(String(500), nullable=False)
    api_key_encrypted = Column(Text, nullable=True)
    is_enabled = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=100)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    provider_data = relationship("ComponentProviderData", back_populates="provider", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('name', name='uq_provider_name'),
    )

    def __repr__(self):
        return f"<ComponentDataProvider(id='{self.id}', name='{self.name}', enabled={self.is_enabled})>"

    @property
    def display_name(self) -> str:
        """Return the provider name for display purposes."""
        return self.name

    @property
    def is_active(self) -> bool:
        """Check if provider is active and enabled."""
        return self.is_enabled

    def to_dict(self, include_api_key: bool = False) -> dict:
        """Convert provider to dictionary for API responses."""
        result = {
            'id': self.id,
            'name': self.name,
            'api_url': self.api_url,
            'is_enabled': self.is_enabled,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        # Only include API key if explicitly requested (for admin purposes)
        if include_api_key:
            result['api_key_encrypted'] = self.api_key_encrypted

        return result
