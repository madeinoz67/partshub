"""
ProjectService with component allocation tracking.
Manages project lifecycle, component allocation, and project-based inventory operations.
"""

import logging
import uuid
from typing import Any

from sqlalchemy import and_, func
from sqlalchemy.orm import Session, selectinload

from ..models import (
    Component,
    Project,
    ProjectComponent,
    ProjectStatus,
    StockTransaction,
)

logger = logging.getLogger(__name__)


class ProjectService:
    """Service layer for project operations and component allocation tracking."""

    def __init__(self, db: Session):
        self.db = db

    def create_project(self, project_data: dict[str, Any]) -> Project:
        """Create a new project."""
        # Generate ID if not provided
        if "id" not in project_data:
            project_data["id"] = str(uuid.uuid4())

        # Create project instance
        project = Project(**project_data)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)

        logger.info(f"Created project: {project.name} ({project.id})")
        return project

    def get_project(self, project_id: str) -> Project | None:
        """Get a project by ID with all relationships loaded."""
        return (
            self.db.query(Project)
            .options(
                selectinload(Project.project_components).selectinload(
                    ProjectComponent.component
                )
            )
            .filter(Project.id == project_id)
            .first()
        )

    def update_project(
        self, project_id: str, update_data: dict[str, Any]
    ) -> Project | None:
        """Update a project."""
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return None

        # Update fields
        for field, value in update_data.items():
            if hasattr(project, field):
                setattr(project, field, value)

        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project_id: str, force: bool = False) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project ID to delete
            force: If True, force delete even with allocated components
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            return False

        # Check for allocated components
        allocated_components = (
            self.db.query(ProjectComponent)
            .filter(ProjectComponent.project_id == project_id)
            .filter(ProjectComponent.quantity_allocated > 0)
            .count()
        )

        if allocated_components > 0 and not force:
            raise ValueError(
                f"Cannot delete project with {allocated_components} allocated components. Use force=True to override."
            )

        # Return all allocated components to inventory before deletion
        if force and allocated_components > 0:
            self._return_all_project_components(project_id)

        self.db.delete(project)
        self.db.commit()
        logger.info(f"Deleted project: {project.name} ({project_id})")
        return True

    def list_projects(
        self,
        status: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Project]:
        """List projects with filtering and pagination."""
        query = self.db.query(Project)

        # Apply filters
        if status:
            query = query.filter(Project.status == status)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Project.name.ilike(search_term) | Project.description.ilike(search_term)
            )

        # Apply sorting
        if sort_order.lower() == "desc":
            if sort_by == "name":
                query = query.order_by(Project.name.desc())
            elif sort_by == "status":
                query = query.order_by(Project.status.desc())
            else:  # created_at
                query = query.order_by(Project.created_at.desc())
        else:
            if sort_by == "name":
                query = query.order_by(Project.name)
            elif sort_by == "status":
                query = query.order_by(Project.status)
            else:  # created_at
                query = query.order_by(Project.created_at)

        # Apply pagination
        query = query.offset(offset).limit(limit)

        return query.all()

    def count_projects(
        self, status: str | None = None, search: str | None = None
    ) -> int:
        """Count projects with filtering."""
        query = self.db.query(Project)

        # Apply filters (same as list_projects)
        if status:
            query = query.filter(Project.status == status)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                Project.name.ilike(search_term) | Project.description.ilike(search_term)
            )

        return query.count()

    def allocate_component_to_project(
        self,
        project_id: str,
        component_id: str,
        quantity: int,
        notes: str | None = None,
    ) -> ProjectComponent:
        """
        Allocate components to a project from inventory.

        Args:
            project_id: Target project ID
            component_id: Component to allocate
            quantity: Quantity to allocate
            notes: Optional allocation notes
        """
        # Validate project exists
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Validate component exists and has sufficient stock
        component = (
            self.db.query(Component).filter(Component.id == component_id).first()
        )
        if not component:
            raise ValueError(f"Component {component_id} not found")

        if component.quantity_on_hand < quantity:
            raise ValueError(
                f"Insufficient stock: {component.quantity_on_hand} available, {quantity} requested"
            )

        # Check if allocation already exists
        existing_allocation = (
            self.db.query(ProjectComponent)
            .filter(
                and_(
                    ProjectComponent.project_id == project_id,
                    ProjectComponent.component_id == component_id,
                )
            )
            .first()
        )

        if existing_allocation:
            # Update existing allocation
            existing_allocation.quantity_allocated += quantity
            if notes:
                existing_allocation.notes = (
                    f"{existing_allocation.notes or ''}\n{notes}".strip()
                )
            project_component = existing_allocation
        else:
            # Create new allocation
            project_component = ProjectComponent(
                project_id=project_id,
                component_id=component_id,
                quantity_allocated=quantity,
                notes=notes,
            )
            self.db.add(project_component)

        # Update component inventory
        component.quantity_on_hand -= quantity

        # Create stock transaction for audit trail
        transaction = StockTransaction.create_remove_transaction(
            component=component,
            quantity=quantity,
            reason=f"Allocated to project: {project.name}",
            reference_id=project_id,
            reference_type="project_allocation",
        )
        self.db.add(transaction)

        self.db.commit()
        self.db.refresh(project_component)

        logger.info(
            f"Allocated {quantity} of {component.part_number} to project {project.name}"
        )
        return project_component

    def return_component_from_project(
        self,
        project_id: str,
        component_id: str,
        quantity: int,
        notes: str | None = None,
    ) -> ProjectComponent:
        """
        Return components from a project to inventory.

        Args:
            project_id: Source project ID
            component_id: Component to return
            quantity: Quantity to return
            notes: Optional return notes
        """
        # Find allocation
        allocation = (
            self.db.query(ProjectComponent)
            .filter(
                and_(
                    ProjectComponent.project_id == project_id,
                    ProjectComponent.component_id == component_id,
                )
            )
            .first()
        )

        if not allocation:
            raise ValueError(
                f"No allocation found for component {component_id} in project {project_id}"
            )

        if allocation.quantity_allocated < quantity:
            raise ValueError(
                f"Cannot return {quantity}: only {allocation.quantity_allocated} allocated"
            )

        # Get project and component for logging
        project = self.db.query(Project).filter(Project.id == project_id).first()
        component = (
            self.db.query(Component).filter(Component.id == component_id).first()
        )

        # Update allocation
        allocation.quantity_allocated -= quantity
        if notes:
            allocation.notes = f"{allocation.notes or ''}\nReturned: {notes}".strip()

        # Update component inventory
        component.quantity_on_hand += quantity

        # Create stock transaction for audit trail
        transaction = StockTransaction.create_add_transaction(
            component=component,
            quantity=quantity,
            reason=f"Returned from project: {project.name}",
            reference_id=project_id,
            reference_type="project_return",
        )
        self.db.add(transaction)

        # Remove allocation if quantity is zero
        if allocation.quantity_allocated == 0:
            self.db.delete(allocation)

        self.db.commit()

        if allocation.quantity_allocated > 0:
            self.db.refresh(allocation)

        logger.info(
            f"Returned {quantity} of {component.part_number} from project {project.name}"
        )
        return allocation

    def get_project_components(self, project_id: str) -> list[ProjectComponent]:
        """Get all component allocations for a project."""
        return (
            self.db.query(ProjectComponent)
            .options(selectinload(ProjectComponent.component))
            .filter(ProjectComponent.project_id == project_id)
            .order_by(ProjectComponent.updated_at)
            .all()
        )

    def get_component_projects(self, component_id: str) -> list[ProjectComponent]:
        """Get all project allocations for a component."""
        return (
            self.db.query(ProjectComponent)
            .options(selectinload(ProjectComponent.project))
            .filter(ProjectComponent.component_id == component_id)
            .filter(ProjectComponent.quantity_allocated > 0)
            .order_by(ProjectComponent.updated_at)
            .all()
        )

    def get_project_statistics(self, project_id: str) -> dict[str, Any]:
        """Get project statistics including component counts and costs."""
        project = self.get_project(project_id)
        if not project:
            return {}

        # Calculate statistics
        total_components = (
            self.db.query(func.count(ProjectComponent.project_id))
            .filter(ProjectComponent.project_id == project_id)
            .scalar()
        )

        total_allocated_quantity = (
            self.db.query(func.sum(ProjectComponent.quantity_allocated))
            .filter(ProjectComponent.project_id == project_id)
            .scalar()
            or 0
        )

        # Calculate estimated cost
        cost_query = (
            self.db.query(
                func.sum(
                    ProjectComponent.quantity_allocated
                    * Component.average_purchase_price
                )
            )
            .join(Component)
            .filter(ProjectComponent.project_id == project_id)
            .scalar()
        )
        estimated_cost = float(cost_query) if cost_query else 0.0

        return {
            "project_id": project_id,
            "project_name": project.name,
            "project_status": project.status,
            "unique_components": total_components,
            "total_allocated_quantity": total_allocated_quantity,
            "estimated_cost": estimated_cost,
            "created_at": project.created_at.isoformat()
            if project.created_at
            else None,
            "updated_at": project.updated_at.isoformat()
            if project.updated_at
            else None,
        }

    def _return_all_project_components(self, project_id: str):
        """Return all allocated components from a project to inventory."""
        allocations = self.get_project_components(project_id)

        for allocation in allocations:
            if allocation.quantity_allocated > 0:
                self.return_component_from_project(
                    project_id,
                    allocation.component_id,
                    allocation.quantity_allocated,
                    "Auto-returned due to project deletion",
                )

    def close_project(
        self, project_id: str, return_components: bool = True
    ) -> Project | None:
        """
        Close a project and optionally return all components to inventory.

        Args:
            project_id: Project to close
            return_components: Whether to return allocated components to inventory
        """
        project = self.get_project(project_id)
        if not project:
            return None

        if return_components:
            self._return_all_project_components(project_id)

        project.status = ProjectStatus.COMPLETED
        self.db.commit()
        self.db.refresh(project)

        logger.info(f"Closed project: {project.name} ({project_id})")
        return project
