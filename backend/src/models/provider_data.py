"""
ComponentProviderData cache model for storing provider data per component.
"""

import uuid
from typing import Any

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class ComponentProviderData(Base):
    """
    Cached provider data per component.

    Stores cached data from external providers including specifications,
    datasheet URLs, images, and provider-specific part identifiers.
    """
    __tablename__ = "component_provider_data"

    # Primary identifier
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key relationships
    component_id = Column(String, ForeignKey('components.id'), nullable=False)
    provider_id = Column(String, ForeignKey('component_data_providers.id'), nullable=False)

    # Provider-specific data
    provider_part_id = Column(String(255), nullable=False)
    datasheet_url = Column(String(1000), nullable=True)
    image_url = Column(String(1000), nullable=True)
    specifications_json = Column(JSON, nullable=True)

    # Cache metadata
    cached_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    component = relationship("Component", back_populates="provider_data_cache")
    provider = relationship("ComponentDataProvider", back_populates="provider_data")

    # Constraints
    __table_args__ = (
        UniqueConstraint('component_id', 'provider_id', name='uq_component_provider'),
        Index('ix_component_provider_cached_at', 'component_id', 'cached_at'),
    )

    def __repr__(self):
        return f"<ComponentProviderData(id='{self.id}', component='{self.component_id}', provider='{self.provider_id}')>"

    @property
    def specifications(self) -> dict[str, Any]:
        """Return specifications as dictionary."""
        return self.specifications_json if self.specifications_json else {}

    @property
    def is_cached_recently(self, hours: int = 24) -> bool:
        """Check if data was cached recently (within specified hours)."""
        from datetime import datetime, timedelta
        if not self.cached_at:
            return False
        return self.cached_at > (datetime.utcnow() - timedelta(hours=hours))

    def update_cache(self,
                    provider_part_id: str,
                    datasheet_url: str | None = None,
                    image_url: str | None = None,
                    specifications: dict[str, Any] | None = None) -> None:
        """Update cached provider data."""
        self.provider_part_id = provider_part_id
        self.datasheet_url = datasheet_url
        self.image_url = image_url
        self.specifications_json = specifications
        self.cached_at = func.now()

    def to_dict(self, include_component: bool = False, include_provider: bool = False) -> dict:
        """Convert provider data to dictionary for API responses."""
        result = {
            'id': self.id,
            'component_id': self.component_id,
            'provider_id': self.provider_id,
            'provider_part_id': self.provider_part_id,
            'datasheet_url': self.datasheet_url,
            'image_url': self.image_url,
            'specifications': self.specifications,
            'cached_at': self.cached_at.isoformat() if self.cached_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        if include_component and self.component:
            result['component'] = {
                'id': self.component.id,
                'name': self.component.name,
                'part_number': self.component.part_number,
                'manufacturer': self.component.manufacturer,
            }

        if include_provider and self.provider:
            result['provider'] = {
                'id': self.provider.id,
                'name': self.provider.name,
                'is_enabled': self.provider.is_enabled,
            }

        return result
