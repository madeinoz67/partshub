"""
KiCadLibraryData model for KiCad-specific component data.
"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
import uuid

from ..database import Base


class KiCadLibraryData(Base):
    """
    KiCad-specific component data for library integration.

    Stores KiCad symbol, footprint, and 3D model references for components,
    enabling seamless integration with KiCad EDA software. Supports component
    library synchronization and automated schematic/PCB design workflows.
    """
    __tablename__ = "kicad_library_data"

    # Primary identifier
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key relationships
    component_id = Column(String, ForeignKey('components.id'), nullable=False, unique=True)

    # KiCad symbol information
    symbol_library = Column(String(255), nullable=True)  # KiCad symbol library name
    symbol_name = Column(String(255), nullable=True)     # Symbol identifier

    # KiCad footprint information
    footprint_library = Column(String(255), nullable=True)  # Footprint library name
    footprint_name = Column(String(255), nullable=True)     # Footprint identifier

    # 3D model information
    model_3d_path = Column(Text, nullable=True)  # 3D model file path

    # Additional KiCad-specific fields stored as JSON
    kicad_fields_json = Column(JSON, nullable=True)  # Additional KiCad-specific fields

    # Relationships
    component = relationship("Component", back_populates="kicad_data")

    def __repr__(self):
        return f"<KiCadLibraryData(component_id={self.component_id}, symbol={self.symbol_name}, footprint={self.footprint_name})>"

    @property
    def has_symbol(self) -> bool:
        """Check if component has KiCad symbol data."""
        return bool(self.symbol_library and self.symbol_name)

    @property
    def has_footprint(self) -> bool:
        """Check if component has KiCad footprint data."""
        return bool(self.footprint_library and self.footprint_name)

    @property
    def has_3d_model(self) -> bool:
        """Check if component has 3D model data."""
        return bool(self.model_3d_path)

    def get_symbol_reference(self) -> str:
        """Get full KiCad symbol reference."""
        if self.has_symbol:
            return f"{self.symbol_library}:{self.symbol_name}"
        return ""

    def get_footprint_reference(self) -> str:
        """Get full KiCad footprint reference."""
        if self.has_footprint:
            return f"{self.footprint_library}:{self.footprint_name}"
        return ""

    def to_kicad_fields(self) -> dict:
        """Convert to KiCad-compatible field format."""
        fields = {
            "Reference": "",  # Will be assigned by KiCad
            "Value": "",      # Will be filled from component
            "Footprint": self.get_footprint_reference(),
        }

        # Add custom KiCad fields from JSON
        if self.kicad_fields_json:
            fields.update(self.kicad_fields_json)

        return fields