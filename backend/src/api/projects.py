"""
Project management API endpoints.
Provides CRUD operations for projects and component allocation tracking.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from ..database import get_db
from ..services.project_service import ProjectService
from ..auth.dependencies import require_auth, require_auth_legacy
from ..models import ProjectStatus

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


# Request/Response models
class ProjectCreate(BaseModel):
    """Create project request."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = ProjectStatus.PLANNING
    version: Optional[str] = None
    client_project_id: Optional[str] = None
    budget_allocated: Optional[float] = None


class ProjectUpdate(BaseModel):
    """Update project request."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    version: Optional[str] = None
    client_project_id: Optional[str] = None
    budget_allocated: Optional[float] = None


class ProjectResponse(BaseModel):
    """Project response model."""
    id: str
    name: str
    description: Optional[str]
    status: ProjectStatus
    version: Optional[str]
    client_project_id: Optional[str]
    budget_allocated: Optional[float]
    budget_spent: float
    start_date: Optional[datetime]
    target_completion_date: Optional[datetime]
    actual_completion_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ComponentAllocationRequest(BaseModel):
    """Component allocation request."""
    component_id: str
    quantity: int = Field(..., gt=0)
    notes: Optional[str] = None


class ComponentReturnRequest(BaseModel):
    """Component return request."""
    component_id: str
    quantity: int = Field(..., gt=0)
    notes: Optional[str] = None


class ProjectComponentResponse(BaseModel):
    """Project component allocation response."""
    project_id: str
    component_id: str
    quantity_allocated: int
    quantity_used: int
    quantity_reserved: int
    notes: Optional[str]
    designator: Optional[str]
    unit_cost_at_allocation: Optional[float]
    created_at: datetime
    updated_at: datetime

    # Include component details
    component_name: Optional[str] = None
    component_part_number: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectStatisticsResponse(BaseModel):
    """Project statistics response."""
    project_id: str
    project_name: str
    project_status: ProjectStatus
    unique_components: int
    total_allocated_quantity: int
    estimated_cost: float
    created_at: Optional[str]
    updated_at: Optional[str]


def validate_uuid(project_id: str) -> None:
    """Validate UUID format and raise 422 error if invalid."""
    try:
        uuid.UUID(project_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid UUID format")


# Project CRUD endpoints
@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(require_auth_legacy),
    db: Session = Depends(get_db)
):
    """Create a new project."""
    project_service = ProjectService(db)

    try:
        project = project_service.create_project(project_data.dict())
        return ProjectResponse.from_orm(project)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by project status"),
    search: Optional[str] = Query(None, description="Search in project name and description"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    limit: int = Query(50, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Result offset for pagination"),
    db: Session = Depends(get_db)
):
    """List projects with filtering and pagination."""
    project_service = ProjectService(db)

    projects = project_service.list_projects(
        status=status_filter,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )

    return [ProjectResponse.from_orm(project) for project in projects]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get project details by ID."""
    validate_uuid(project_id)

    project_service = ProjectService(db)
    project = project_service.get_project(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return ProjectResponse.from_orm(project)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_user: dict = Depends(require_auth_legacy),
    db: Session = Depends(get_db)
):
    """Update project details."""
    validate_uuid(project_id)

    project_service = ProjectService(db)

    # Filter out None values
    update_data = {k: v for k, v in project_update.dict().items() if v is not None}

    project = project_service.update_project(project_id, update_data)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return ProjectResponse.from_orm(project)


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    force: bool = Query(False, description="Force delete even with allocated components"),
    current_user: dict = Depends(require_auth_legacy),
    db: Session = Depends(get_db)
):
    """Delete a project."""
    validate_uuid(project_id)

    project_service = ProjectService(db)

    try:
        success = project_service.delete_project(project_id, force=force)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        return {"message": "Project deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Component allocation endpoints
@router.post("/{project_id}/allocate", response_model=ProjectComponentResponse)
async def allocate_component(
    project_id: str,
    allocation: ComponentAllocationRequest,
    current_user: dict = Depends(require_auth_legacy),
    db: Session = Depends(get_db)
):
    """Allocate components to a project."""
    validate_uuid(project_id)

    project_service = ProjectService(db)

    try:
        project_component = project_service.allocate_component_to_project(
            project_id=project_id,
            component_id=allocation.component_id,
            quantity=allocation.quantity,
            notes=allocation.notes
        )

        # Create response with component details
        response_data = ProjectComponentResponse.from_orm(project_component)
        if project_component.component:
            response_data.component_name = project_component.component.name
            response_data.component_part_number = project_component.component.part_number

        return response_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{project_id}/return", response_model=ProjectComponentResponse)
async def return_component(
    project_id: str,
    return_request: ComponentReturnRequest,
    current_user: dict = Depends(require_auth_legacy),
    db: Session = Depends(get_db)
):
    """Return components from a project to inventory."""
    validate_uuid(project_id)

    project_service = ProjectService(db)

    try:
        project_component = project_service.return_component_from_project(
            project_id=project_id,
            component_id=return_request.component_id,
            quantity=return_request.quantity,
            notes=return_request.notes
        )

        # Create response with component details
        response_data = ProjectComponentResponse.from_orm(project_component)
        if project_component.component:
            response_data.component_name = project_component.component.name
            response_data.component_part_number = project_component.component.part_number

        return response_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{project_id}/components", response_model=List[ProjectComponentResponse])
async def get_project_components(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get all component allocations for a project."""
    validate_uuid(project_id)

    project_service = ProjectService(db)
    project_components = project_service.get_project_components(project_id)

    # Create responses with component details
    responses = []
    for pc in project_components:
        response_data = ProjectComponentResponse.from_orm(pc)
        if pc.component:
            response_data.component_name = pc.component.name
            response_data.component_part_number = pc.component.part_number
        responses.append(response_data)

    return responses


@router.get("/{project_id}/statistics", response_model=ProjectStatisticsResponse)
async def get_project_statistics(
    project_id: str,
    db: Session = Depends(get_db)
):
    """Get project statistics including component counts and costs."""
    validate_uuid(project_id)

    project_service = ProjectService(db)
    stats = project_service.get_project_statistics(project_id)

    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return ProjectStatisticsResponse(**stats)


@router.post("/{project_id}/close")
async def close_project(
    project_id: str,
    return_components: bool = Query(True, description="Whether to return allocated components to inventory"),
    current_user: dict = Depends(require_auth_legacy),
    db: Session = Depends(get_db)
):
    """Close a project and optionally return components to inventory."""
    validate_uuid(project_id)

    project_service = ProjectService(db)
    project = project_service.close_project(project_id, return_components=return_components)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )

    return {
        "message": "Project closed successfully",
        "components_returned": return_components
    }