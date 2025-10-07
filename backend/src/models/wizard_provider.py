"""
Provider model for wizard feature external provider management.

This is separate from ComponentDataProvider to maintain the wizard feature's
specific requirements for provider adapters and external service integration.
"""

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Provider(Base):
    """
    External provider configuration for wizard feature.

    Manages configuration for external component providers (LCSC, Mouser, DigiKey)
    that can be searched and linked during component creation via the wizard.
    """

    __tablename__ = "providers"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Provider information
    name = Column(String(100), nullable=False, unique=True, index=True)
    adapter_class = Column(
        String(200), nullable=False
    )  # Python class name for adapter (e.g., "LCSCAdapter")
    base_url = Column(String(500), nullable=False)  # Base API URL
    api_key_required = Column(Boolean, nullable=False, default=True)
    status = Column(
        String(20),
        nullable=False,
        default="active",
        index=True,
    )

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    provider_links = relationship(
        "ProviderLink",
        back_populates="provider",
        cascade="all, delete-orphan",
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'inactive')",
            name="ck_providers_status_valid",
        ),
    )

    def __repr__(self):
        return f"<Provider(id={self.id}, name='{self.name}', status='{self.status}')>"

    @property
    def is_active(self) -> bool:
        """Check if provider is active."""
        return self.status == "active"
