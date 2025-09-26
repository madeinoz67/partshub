"""
Project model and ProjectComponent junction for component allocation tracking.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Numeric, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from ..database import Base


class ProjectStatus(enum.Enum):
    """Project status enumeration."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Project(Base):
    """
    Project model for tracking component allocation and usage across different builds/designs.
    """
    __tablename__ = "projects"

    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Project metadata
    status = Column(SQLEnum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNING)
    version = Column(String(20), nullable=True)  # v1.0, rev-A, etc.
    client_project_id = Column(String(100), nullable=True)  # External reference

    # Budgeting
    budget_allocated = Column(Numeric(10, 2), nullable=True)
    budget_spent = Column(Numeric(10, 2), nullable=False, default=0)

    # Dates
    start_date = Column(DateTime(timezone=True), nullable=True)
    target_completion_date = Column(DateTime(timezone=True), nullable=True)
    actual_completion_date = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    project_components = relationship("ProjectComponent", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id='{self.id}', name='{self.name}', status='{self.status.value}')>"

    @property
    def total_component_count(self):
        """Get total count of all components allocated to this project."""
        return sum(pc.quantity_allocated for pc in self.project_components)

    @property
    def unique_component_count(self):
        """Get count of unique components in this project."""
        return len(self.project_components)

    @property
    def estimated_component_cost(self):
        """Calculate estimated cost of all allocated components."""
        total_cost = 0
        for pc in self.project_components:
            if pc.component.average_purchase_price:
                total_cost += pc.component.average_purchase_price * pc.quantity_allocated
        return total_cost

    @property
    def is_over_budget(self):
        """Check if project spending exceeds allocated budget."""
        if not self.budget_allocated:
            return False
        return self.budget_spent > self.budget_allocated

    @property
    def budget_remaining(self):
        """Calculate remaining budget (can be negative)."""
        if not self.budget_allocated:
            return None
        return self.budget_allocated - self.budget_spent


class ProjectComponent(Base):
    """
    Junction table tracking component allocation and usage in projects.
    """
    __tablename__ = "project_components"

    # Composite primary key
    project_id = Column(String, ForeignKey("projects.id"), primary_key=True)
    component_id = Column(String, ForeignKey("components.id"), primary_key=True)

    # Allocation tracking
    quantity_allocated = Column(Integer, nullable=False, default=1)
    quantity_used = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, nullable=False, default=0)  # Reserved from inventory

    # Component-specific project notes
    notes = Column(Text, nullable=True)
    designator = Column(String(50), nullable=True)  # PCB reference designator (R1, C5, U3, etc.)

    # Cost tracking
    unit_cost_at_allocation = Column(Numeric(10, 4), nullable=True)  # Cost when allocated
    total_cost_allocated = Column(Numeric(10, 2), nullable=True)

    # Timestamps
    allocated_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="project_components")
    component = relationship("Component", back_populates="project_components")

    def __repr__(self):
        return f"<ProjectComponent(project_id='{self.project_id}', component_id='{self.component_id}', qty={self.quantity_allocated})>"

    @property
    def quantity_remaining(self):
        """Calculate remaining quantity not yet used."""
        return self.quantity_allocated - self.quantity_used

    @property
    def is_fully_used(self):
        """Check if all allocated components have been used."""
        return self.quantity_used >= self.quantity_allocated

    @property
    def usage_percentage(self):
        """Calculate percentage of allocated components that have been used."""
        if self.quantity_allocated == 0:
            return 0
        return (self.quantity_used / self.quantity_allocated) * 100

    @property
    def can_reserve_from_stock(self):
        """Check if there's enough stock to reserve the allocated quantity."""
        available_stock = self.component.quantity_on_hand - self.quantity_reserved
        return available_stock >= (self.quantity_allocated - self.quantity_reserved)