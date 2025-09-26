"""
Attachment model for component files (datasheets, photos, etc.).
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from ..database import Base


class Attachment(Base):
    """
    Attachment model for storing component-related files.
    """
    __tablename__ = "attachments"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    component_id = Column(String, ForeignKey("components.id"), nullable=False)

    # File information
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)  # Relative path to file storage

    # Metadata
    title = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    attachment_type = Column(String(50), nullable=True)  # datasheet, photo, schematic, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    component = relationship("Component", back_populates="attachments")

    def __repr__(self):
        return f"<Attachment(id='{self.id}', filename='{self.filename}', component_id='{self.component_id}')>"