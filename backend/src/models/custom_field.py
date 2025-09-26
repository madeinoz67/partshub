"""
CustomField and CustomFieldValue models for user-defined component attributes.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base


class FieldType(enum.Enum):
    """Custom field type enumeration."""
    TEXT = "text"
    NUMBER = "number"
    BOOLEAN = "boolean"
    DATE = "date"
    SELECT = "select"  # Single choice from options
    MULTI_SELECT = "multi_select"  # Multiple choices from options


class CustomField(Base):
    """
    Definition of custom fields that can be added to components.
    """
    __tablename__ = "custom_fields"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    field_type = Column(SQLEnum(FieldType), nullable=False)

    # Configuration
    is_required = Column(String, nullable=False, default=False)
    default_value = Column(Text, nullable=True)
    validation_rules = Column(Text, nullable=True)  # JSON string with validation rules
    options = Column(Text, nullable=True)  # JSON array for SELECT/MULTI_SELECT types

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    values = relationship("CustomFieldValue", back_populates="field", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CustomField(id='{self.id}', name='{self.name}', type='{self.field_type.value}')>"


class CustomFieldValue(Base):
    """
    Values of custom fields for specific components.
    """
    __tablename__ = "custom_field_values"

    # Composite primary key
    component_id = Column(String, ForeignKey("components.id"), primary_key=True)
    field_id = Column(String, ForeignKey("custom_fields.id"), primary_key=True)

    # Value storage (all values stored as text, converted based on field type)
    value = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    component = relationship("Component", back_populates="custom_field_values")
    field = relationship("CustomField", back_populates="values")

    def __repr__(self):
        return f"<CustomFieldValue(component_id='{self.component_id}', field_id='{self.field_id}', value='{self.value}')>"