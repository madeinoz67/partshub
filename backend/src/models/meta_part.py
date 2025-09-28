"""
MetaPart and MetaPartComponent models for assembly/BOM management.
"""

import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from ..database import Base


class MetaPart(Base):
    """
    Assembly/BOM management for complex electronic systems.

    Represents a higher-level assembly or sub-assembly composed of multiple
    components. Enables hierarchical BOM management, cost calculation, and
    availability tracking for complete electronic assemblies.
    """
    __tablename__ = "meta_parts"

    # Primary identifier
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Assembly information
    name = Column(String(255), nullable=False, index=True)  # Assembly name
    description = Column(Text, nullable=True)              # Assembly description
    version = Column(String(50), nullable=True)            # Assembly version (e.g., "v2.1", "rev_A")

    # Assembly metadata
    assembly_type = Column(String(100), nullable=True)     # PCB, mechanical, cable, etc.
    reference_designator = Column(String(50), nullable=True)  # Circuit reference (e.g., "U1", "PCB1")
    notes = Column(Text, nullable=True)

    # Relationships
    components = relationship("MetaPartComponent", back_populates="meta_part", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_meta_part_name_version'),
    )

    def __repr__(self):
        return f"<MetaPart(name='{self.name}', version='{self.version}')>"

    @property
    def display_name(self):
        """Human-readable display name including version."""
        if self.version:
            return f"{self.name} {self.version}"
        return self.name

    @property
    def total_component_count(self) -> int:
        """Total number of individual components in this assembly."""
        return sum(comp.quantity_required for comp in self.components)

    @property
    def unique_component_count(self) -> int:
        """Number of unique component types in this assembly."""
        return len(self.components)

    def calculate_total_cost(self) -> float:
        """Calculate total cost of assembly based on component costs."""
        total = 0.0
        for meta_comp in self.components:
            if meta_comp.component and meta_comp.component.average_purchase_price:
                component_cost = float(meta_comp.component.average_purchase_price)
                total += component_cost * meta_comp.quantity_required
        return total

    def check_availability(self) -> dict:
        """Check if all components are available for assembly."""
        availability = {
            'can_build': True,
            'max_quantity': float('inf'),
            'missing_components': [],
            'low_stock_components': []
        }

        for meta_comp in self.components:
            component = meta_comp.component
            if not component:
                availability['can_build'] = False
                availability['missing_components'].append({
                    'component_name': f"Component {meta_comp.component_id} (not found)"
                })
                continue

            # Check if we have enough stock
            available_qty = component.quantity_on_hand
            required_qty = meta_comp.quantity_required

            if available_qty < required_qty:
                availability['can_build'] = False
                availability['missing_components'].append({
                    'component_name': component.name,
                    'required': required_qty,
                    'available': available_qty,
                    'shortage': required_qty - available_qty
                })
            else:
                # Calculate how many assemblies we can build
                possible_assemblies = available_qty // required_qty
                availability['max_quantity'] = min(availability['max_quantity'], possible_assemblies)

                # Check for low stock warning
                if component.is_low_stock:
                    availability['low_stock_components'].append({
                        'component_name': component.name,
                        'current_stock': available_qty,
                        'minimum_stock': component.minimum_stock
                    })

        if availability['max_quantity'] == float('inf'):
            availability['max_quantity'] = 0

        return availability


class MetaPartComponent(Base):
    """
    Junction table for assembly composition.

    Links MetaParts to their constituent Components with quantity requirements.
    Enables BOM tracking, cost calculation, and availability analysis.
    """
    __tablename__ = "meta_part_components"

    # Primary identifier
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign key relationships
    meta_part_id = Column(String, ForeignKey('meta_parts.id'), nullable=False)
    component_id = Column(String, ForeignKey('components.id'), nullable=False)

    # Quantity requirements
    quantity_required = Column(Integer, nullable=False, default=1)  # Required quantity in assembly

    # Component-specific assembly notes
    assembly_notes = Column(Text, nullable=True)  # Special handling, placement notes, etc.
    reference_designators = Column(String(255), nullable=True)  # PCB reference designators (e.g., "R1,R2,R3")

    # Relationships
    meta_part = relationship("MetaPart", back_populates="components")
    component = relationship("Component")

    # Constraints
    __table_args__ = (
        UniqueConstraint('meta_part_id', 'component_id', name='uq_meta_part_component'),
    )

    def __repr__(self):
        return f"<MetaPartComponent(meta_part_id='{self.meta_part_id}', component_id='{self.component_id}', qty={self.quantity_required})>"

    @property
    def component_cost(self) -> float:
        """Calculate total cost for this component in the assembly."""
        if self.component and self.component.average_purchase_price:
            return float(self.component.average_purchase_price) * self.quantity_required
        return 0.0

    @property
    def is_available(self) -> bool:
        """Check if sufficient quantity is available."""
        if not self.component:
            return False
        return self.component.quantity_on_hand >= self.quantity_required

    @property
    def available_assemblies(self) -> int:
        """Number of assemblies possible with current stock."""
        if not self.component or self.quantity_required <= 0:
            return 0
        return self.component.quantity_on_hand // self.quantity_required
