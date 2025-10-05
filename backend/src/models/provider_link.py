"""
ProviderLink model for linking components to external providers.

Represents the association between a component and an external provider,
tracking synchronization status and provider-specific metadata.
"""

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class ProviderLink(Base):
    """
    Link between a component and an external provider.

    Tracks the relationship between a PartsHub component and an external
    provider's part listing, including synchronization status and metadata.
    """

    __tablename__ = "provider_links"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    component_id = Column(
        String,
        ForeignKey("components.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_id = Column(
        Integer,
        ForeignKey("providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Provider link information
    provider_part_number = Column(
        String(100), nullable=False, index=True
    )  # Part number in provider's system
    provider_url = Column(String(500), nullable=False)  # Direct URL to part on provider
    sync_status = Column(
        String(20),
        nullable=False,
        default="pending",
    )  # synced, pending, failed
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    provider_metadata = Column(
        "metadata", JSON, nullable=True
    )  # Provider-specific metadata (pricing, etc.)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    component = relationship("Component", back_populates="provider_links")
    provider = relationship("Provider", back_populates="provider_links")
    resources = relationship(
        "Resource",
        back_populates="provider_link",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "component_id",
            "provider_id",
            name="uq_provider_links_component_id_provider_id",
        ),
        CheckConstraint(
            "sync_status IN ('synced', 'pending', 'failed')",
            name="ck_provider_links_sync_status_valid",
        ),
    )

    def __repr__(self):
        return f"<ProviderLink(id={self.id}, component_id='{self.component_id}', provider_id={self.provider_id}, status='{self.sync_status}')>"

    @property
    def is_synced(self) -> bool:
        """Check if link is successfully synced."""
        return self.sync_status == "synced"
