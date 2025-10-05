"""
Resource model for managing provider-linked files (datasheets, images, etc.).

Tracks downloadable resources associated with provider links, including
download status and file metadata.
"""

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..database import Base


class Resource(Base):
    """
    Downloadable resource associated with a provider link.

    Tracks files such as datasheets, images, footprints, symbols, and 3D models
    that are linked to a component via a provider.
    """

    __tablename__ = "resources"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign key
    provider_link_id = Column(
        Integer,
        ForeignKey("provider_links.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Resource information
    resource_type = Column(
        String(20), nullable=False
    )  # datasheet, image, footprint, symbol, model_3d
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)  # Local file path after download
    source_url = Column(String(500), nullable=False)  # Original URL
    download_status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )  # pending, downloading, complete, failed
    file_size_bytes = Column(Integer, nullable=True)
    downloaded_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    provider_link = relationship("ProviderLink", back_populates="resources")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "resource_type IN ('datasheet', 'image', 'footprint', 'symbol', 'model_3d')",
            name="ck_resources_resource_type_valid",
        ),
        CheckConstraint(
            "download_status IN ('pending', 'downloading', 'complete', 'failed')",
            name="ck_resources_download_status_valid",
        ),
    )

    def __repr__(self):
        return f"<Resource(id={self.id}, type='{self.resource_type}', status='{self.download_status}')>"

    @property
    def is_downloaded(self) -> bool:
        """Check if resource is successfully downloaded."""
        return self.download_status == "complete"

    @property
    def is_pending(self) -> bool:
        """Check if resource is pending download."""
        return self.download_status == "pending"
