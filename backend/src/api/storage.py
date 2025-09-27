"""
Storage locations API endpoints implementing the OpenAPI specification.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uuid

from ..database import get_db
from ..services.storage_service import StorageLocationService
from ..auth import require_auth, get_optional_user

# Pydantic schemas
class StorageLocationBase(BaseModel):
    name: str
    description: Optional[str] = None
    type: str  # container, room, building, cabinet, drawer, shelf, bin
    parent_id: Optional[str] = None
    qr_code_id: Optional[str] = None

class StorageLocationCreate(StorageLocationBase):
    pass

class StorageLocationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    parent_id: Optional[str] = None
    qr_code_id: Optional[str] = None

class StorageLocationResponse(StorageLocationBase):
    id: str
    location_hierarchy: str
    created_at: str
    updated_at: str
    children: Optional[List[dict]] = None
    component_count: Optional[int] = None
    full_hierarchy_path: Optional[List[dict]] = None

    class Config:
        from_attributes = True

class BulkCreateLocation(BaseModel):
    name: str
    description: Optional[str] = None
    type: str
    parent_name: Optional[str] = None  # Reference by name instead of ID
    qr_code_id: Optional[str] = None

class BulkCreateRequest(BaseModel):
    locations: List[BulkCreateLocation]

router = APIRouter(prefix="/api/v1/storage-locations", tags=["storage"])

# Authentication implemented - using real auth system

@router.get("", response_model=List[StorageLocationResponse])
def list_storage_locations(
    search: Optional[str] = Query(None, description="Search in name or hierarchy"),
    type: Optional[str] = Query(None, description="Filter by location type"),
    include_component_count: bool = Query(False, description="Include component counts"),
    limit: int = Query(100, ge=1, le=200, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db)
):
    """List storage locations with filtering and pagination."""
    # Validate type if provided
    valid_types = ["container", "room", "building", "cabinet", "drawer", "shelf", "bin"]
    if type and type not in valid_types:
        raise HTTPException(status_code=422, detail=f"Invalid type. Must be one of: {valid_types}")

    service = StorageLocationService(db)
    locations = service.list_storage_locations(
        search=search,
        location_type=type,
        include_component_count=include_component_count,
        limit=limit,
        offset=offset
    )

    # Convert to response format
    result = []
    for location in locations:
        location_dict = {
            "id": location.id,
            "name": location.name,
            "description": location.description,
            "type": location.type,
            "parent_id": location.parent_id,
            "location_hierarchy": location.location_hierarchy,
            "qr_code_id": location.qr_code_id,
            "created_at": location.created_at.isoformat(),
            "updated_at": location.updated_at.isoformat()
        }

        if include_component_count:
            location_dict["component_count"] = getattr(location, 'component_count', 0)

        result.append(location_dict)

    return result

@router.post("", response_model=StorageLocationResponse, status_code=status.HTTP_201_CREATED)
def create_storage_location(
    location: StorageLocationCreate,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new storage location."""
    # Validate type
    valid_types = ["container", "room", "building", "cabinet", "drawer", "shelf", "bin"]
    if location.type not in valid_types:
        raise HTTPException(status_code=422, detail=f"Invalid type. Must be one of: {valid_types}")

    # Validate parent_id if provided
    if location.parent_id:
        try:
            uuid.UUID(location.parent_id)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid parent_id format")

    service = StorageLocationService(db)

    try:
        created_location = service.create_storage_location(location.model_dump())
        return {
            "id": created_location.id,
            "name": created_location.name,
            "description": created_location.description,
            "type": created_location.type,
            "parent_id": created_location.parent_id,
            "location_hierarchy": created_location.location_hierarchy,
            "qr_code_id": created_location.qr_code_id,
            "created_at": created_location.created_at.isoformat(),
            "updated_at": created_location.updated_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/bulk-create", response_model=List[StorageLocationResponse], status_code=status.HTTP_201_CREATED)
def bulk_create_storage_locations(
    request: BulkCreateRequest,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Bulk create storage locations with hierarchy support."""
    if not request.locations:
        raise HTTPException(status_code=422, detail="No locations provided")

    # Validate all locations
    valid_types = ["container", "room", "building", "cabinet", "drawer", "shelf", "bin"]
    for location in request.locations:
        if location.type not in valid_types:
            raise HTTPException(status_code=422, detail=f"Invalid type '{location.type}'. Must be one of: {valid_types}")

    service = StorageLocationService(db)

    try:
        created_locations = service.bulk_create_locations([loc.model_dump() for loc in request.locations])
        return created_locations
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{location_id}", response_model=StorageLocationResponse)
def get_storage_location(
    location_id: str,
    include_children: bool = Query(False, description="Include child locations"),
    include_component_count: bool = Query(False, description="Include component count"),
    include_full_hierarchy: bool = Query(False, description="Include full hierarchy path"),
    db: Session = Depends(get_db)
):
    """Get a storage location by ID."""
    try:
        uuid.UUID(location_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid location ID format")

    service = StorageLocationService(db)
    location = service.get_storage_location(
        location_id,
        include_children=include_children,
        include_component_count=include_component_count,
        include_full_hierarchy=include_full_hierarchy
    )

    if not location:
        raise HTTPException(status_code=404, detail="Storage location not found")

    # Convert to response format
    result = {
        "id": location.id,
        "name": location.name,
        "description": location.description,
        "type": location.type,
        "parent_id": location.parent_id,
        "location_hierarchy": location.location_hierarchy,
        "qr_code_id": location.qr_code_id,
        "created_at": location.created_at.isoformat(),
        "updated_at": location.updated_at.isoformat()
    }

    if include_children and hasattr(location, 'children'):
        result["children"] = [
            {
                "id": child.id,
                "name": child.name,
                "type": child.type,
                "parent_id": child.parent_id
            } for child in location.children
        ]

    if include_component_count:
        result["component_count"] = getattr(location, 'component_count', 0)

    if include_full_hierarchy:
        result["full_hierarchy_path"] = getattr(location, 'full_hierarchy_path', [])

    return result

@router.put("/{location_id}", response_model=StorageLocationResponse)
def update_storage_location(
    location_id: str,
    location_update: StorageLocationUpdate,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update a storage location."""
    try:
        uuid.UUID(location_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid location ID format")

    # Filter out None values
    update_data = {k: v for k, v in location_update.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=422, detail="No data provided for update")

    # Validate type if provided
    if "type" in update_data:
        valid_types = ["container", "room", "building", "cabinet", "drawer", "shelf", "bin"]
        if update_data["type"] not in valid_types:
            raise HTTPException(status_code=422, detail=f"Invalid type. Must be one of: {valid_types}")

    # Validate parent_id if provided
    if "parent_id" in update_data and update_data["parent_id"]:
        try:
            uuid.UUID(update_data["parent_id"])
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid parent_id format")

    service = StorageLocationService(db)

    try:
        updated_location = service.update_storage_location(location_id, update_data)
        if not updated_location:
            raise HTTPException(status_code=404, detail="Storage location not found")
        return updated_location
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{location_id}/components")
def get_location_components(
    location_id: str,
    include_children: bool = Query(False, description="Include components from child locations"),
    search: Optional[str] = Query(None, description="Search in component names"),
    category: Optional[str] = Query(None, description="Filter by category"),
    component_type: Optional[str] = Query(None, description="Filter by component type"),
    stock_status: Optional[str] = Query(None, pattern="^(low|out|available)$", description="Filter by stock status"),
    sort_by: str = Query("name", pattern="^(name|quantity)$", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    limit: int = Query(50, ge=1, le=100, description="Number of components to return"),
    offset: int = Query(0, ge=0, description="Number of components to skip"),
    db: Session = Depends(get_db)
):
    """Get components in a storage location."""
    try:
        uuid.UUID(location_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid location ID format")

    service = StorageLocationService(db)

    # Check if location exists
    location = service.get_storage_location(location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Storage location not found")

    components = service.get_location_components(
        location_id=location_id,
        include_children=include_children,
        search=search,
        category=category,
        component_type=component_type,
        stock_status=stock_status,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )

    # Convert to response format (similar to components API)
    result = []
    for component in components:
        # Get the ComponentLocation record for this specific location
        from ..models import ComponentLocation
        component_location = db.query(ComponentLocation).filter(
            ComponentLocation.component_id == component.id,
            ComponentLocation.storage_location_id == location_id
        ).first()

        # Use location-specific quantities if available, otherwise use component totals
        location_quantity = component_location.quantity_on_hand if component_location else 0
        location_minimum = component_location.minimum_stock if component_location else 0

        component_dict = {
            "id": component.id,
            "name": component.name,
            "part_number": component.part_number,
            "manufacturer": component.manufacturer,
            "component_type": component.component_type,
            "quantity_on_hand": location_quantity,
            "minimum_stock": location_minimum,
            "storage_location": {
                "id": component.primary_location.id,
                "name": component.primary_location.name,
                "location_hierarchy": component.primary_location.location_hierarchy
            } if component.primary_location else None,
            "category": {
                "id": component.category.id,
                "name": component.category.name
            } if component.category else None
        }
        result.append(component_dict)

    return result