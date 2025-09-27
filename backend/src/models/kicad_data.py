"""
KiCadLibraryData model for KiCad-specific component data.
"""

from sqlalchemy import Column, String, Text, ForeignKey, JSON, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from ..database import Base


class KiCadDataSource(enum.Enum):
    """Source of KiCad data with priority order."""
    CUSTOM = "custom"           # User uploaded files (highest priority)
    PROVIDER = "provider"       # Downloaded from component provider
    AUTO_GENERATED = "auto"     # System generated (lowest priority)


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

    # Custom file storage for symbols and footprints
    custom_symbol_file_path = Column(Text, nullable=True)      # Path to custom .kicad_sym file
    custom_footprint_file_path = Column(Text, nullable=True)   # Path to custom .kicad_mod file
    custom_3d_model_file_path = Column(Text, nullable=True)    # Path to custom 3D model file

    # Source tracking with priority order
    symbol_source = Column(Enum(KiCadDataSource), default=KiCadDataSource.AUTO_GENERATED, nullable=False)
    footprint_source = Column(Enum(KiCadDataSource), default=KiCadDataSource.AUTO_GENERATED, nullable=False)
    model_3d_source = Column(Enum(KiCadDataSource), default=KiCadDataSource.AUTO_GENERATED, nullable=False)

    # Timestamps for tracking changes
    symbol_updated_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    footprint_updated_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    model_3d_updated_at = Column(DateTime, default=datetime.utcnow, nullable=True)

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

    def get_effective_symbol_path(self) -> str:
        """Get the effective symbol path based on source priority."""
        if self.symbol_source == KiCadDataSource.CUSTOM and self.custom_symbol_file_path:
            return self.custom_symbol_file_path
        elif self.symbol_source == KiCadDataSource.PROVIDER and self.has_symbol:
            return self.get_symbol_reference()
        elif self.has_symbol:
            return self.get_symbol_reference()
        return ""

    def get_effective_footprint_path(self) -> str:
        """Get the effective footprint path based on source priority."""
        if self.footprint_source == KiCadDataSource.CUSTOM and self.custom_footprint_file_path:
            return self.custom_footprint_file_path
        elif self.footprint_source == KiCadDataSource.PROVIDER and self.has_footprint:
            return self.get_footprint_reference()
        elif self.has_footprint:
            return self.get_footprint_reference()
        return ""

    def get_effective_3d_model_path(self) -> str:
        """Get the effective 3D model path based on source priority."""
        if self.model_3d_source == KiCadDataSource.CUSTOM and self.custom_3d_model_file_path:
            return self.custom_3d_model_file_path
        elif self.model_3d_source == KiCadDataSource.PROVIDER and self.model_3d_path:
            return self.model_3d_path
        elif self.model_3d_path:
            return self.model_3d_path
        return ""

    def set_custom_symbol(self, file_path: str) -> None:
        """Set custom symbol file and update source tracking."""
        self.custom_symbol_file_path = file_path
        self.symbol_source = KiCadDataSource.CUSTOM
        self.symbol_updated_at = datetime.utcnow()

    def set_custom_footprint(self, file_path: str) -> None:
        """Set custom footprint file and update source tracking."""
        self.custom_footprint_file_path = file_path
        self.footprint_source = KiCadDataSource.CUSTOM
        self.footprint_updated_at = datetime.utcnow()

    def set_custom_3d_model(self, file_path: str) -> None:
        """Set custom 3D model file and update source tracking."""
        self.custom_3d_model_file_path = file_path
        self.model_3d_source = KiCadDataSource.CUSTOM
        self.model_3d_updated_at = datetime.utcnow()

    def reset_symbol_to_auto(self) -> None:
        """Reset symbol to auto-generated, removing custom override."""
        self.custom_symbol_file_path = None
        self.symbol_source = KiCadDataSource.AUTO_GENERATED
        self.symbol_updated_at = datetime.utcnow()

    def reset_footprint_to_auto(self) -> None:
        """Reset footprint to auto-generated, removing custom override."""
        self.custom_footprint_file_path = None
        self.footprint_source = KiCadDataSource.AUTO_GENERATED
        self.footprint_updated_at = datetime.utcnow()

    def reset_3d_model_to_auto(self) -> None:
        """Reset 3D model to auto-generated, removing custom override."""
        self.custom_3d_model_file_path = None
        self.model_3d_source = KiCadDataSource.AUTO_GENERATED
        self.model_3d_updated_at = datetime.utcnow()

    def set_provider_data(self, symbol_lib: str = None, symbol_name: str = None,
                         footprint_lib: str = None, footprint_name: str = None,
                         model_3d_path: str = None) -> None:
        """Set provider data and update source tracking (only if not custom)."""
        if self.symbol_source != KiCadDataSource.CUSTOM and symbol_lib and symbol_name:
            self.symbol_library = symbol_lib
            self.symbol_name = symbol_name
            self.symbol_source = KiCadDataSource.PROVIDER
            self.symbol_updated_at = datetime.utcnow()

        if self.footprint_source != KiCadDataSource.CUSTOM and footprint_lib and footprint_name:
            self.footprint_library = footprint_lib
            self.footprint_name = footprint_name
            self.footprint_source = KiCadDataSource.PROVIDER
            self.footprint_updated_at = datetime.utcnow()

        if self.model_3d_source != KiCadDataSource.CUSTOM and model_3d_path:
            self.model_3d_path = model_3d_path
            self.model_3d_source = KiCadDataSource.PROVIDER
            self.model_3d_updated_at = datetime.utcnow()

    @property
    def has_custom_symbol(self) -> bool:
        """Check if component has custom symbol file."""
        return self.symbol_source == KiCadDataSource.CUSTOM and bool(self.custom_symbol_file_path)

    @property
    def has_custom_footprint(self) -> bool:
        """Check if component has custom footprint file."""
        return self.footprint_source == KiCadDataSource.CUSTOM and bool(self.custom_footprint_file_path)

    @property
    def has_custom_3d_model(self) -> bool:
        """Check if component has custom 3D model file."""
        return self.model_3d_source == KiCadDataSource.CUSTOM and bool(self.custom_3d_model_file_path)

    def to_kicad_fields(self) -> dict:
        """Convert to KiCad-compatible field format."""
        fields = {
            "Reference": "",  # Will be assigned by KiCad
            "Value": "",      # Will be filled from component
            "Footprint": self.get_effective_footprint_path(),
        }

        # Add custom KiCad fields from JSON
        if self.kicad_fields_json:
            fields.update(self.kicad_fields_json)

        return fields

    def get_source_info(self) -> dict:
        """Get comprehensive source information for debugging/UI."""
        return {
            "symbol": {
                "source": self.symbol_source.value,
                "has_custom": self.has_custom_symbol,
                "has_library": self.has_symbol,
                "effective_path": self.get_effective_symbol_path(),
                "updated_at": self.symbol_updated_at.isoformat() if self.symbol_updated_at else None
            },
            "footprint": {
                "source": self.footprint_source.value,
                "has_custom": self.has_custom_footprint,
                "has_library": self.has_footprint,
                "effective_path": self.get_effective_footprint_path(),
                "updated_at": self.footprint_updated_at.isoformat() if self.footprint_updated_at else None
            },
            "model_3d": {
                "source": self.model_3d_source.value,
                "has_custom": self.has_custom_3d_model,
                "has_library": self.has_3d_model,
                "effective_path": self.get_effective_3d_model_path(),
                "updated_at": self.model_3d_updated_at.isoformat() if self.model_3d_updated_at else None
            }
        }