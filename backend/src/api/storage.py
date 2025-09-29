"""
Storage locations API endpoints implementing the OpenAPI specification.
"""

import uuid
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth.dependencies import require_auth
from ..database import get_db
from ..services.storage_service import StorageLocationService


# Enums for validation and OpenAPI documentation
class StorageLocationType(str, Enum):
    """Valid storage location types matching database constraints."""

    CONTAINER = "container"
    ROOM = "room"
    BUILDING = "building"
    CABINET = "cabinet"
    DRAWER = "drawer"
    SHELF = "shelf"
    BIN = "bin"


# Pydantic schemas
class StorageLocationBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Storage location name"
    )
    description: str | None = Field(
        None, max_length=500, description="Optional description"
    )
    type: StorageLocationType = Field(..., description="Storage location type")
    parent_id: str | None = Field(None, description="Parent storage location ID")
    qr_code_id: str | None = Field(
        None, max_length=50, description="QR code identifier"
    )

    @field_validator("parent_id")
    @classmethod
    def validate_parent_id(cls, v):  # noqa: N805
        """Validate parent_id is a valid UUID if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError("parent_id must be a valid UUID")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):  # noqa: N805
        """Ensure name is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()


class StorageLocationCreate(StorageLocationBase):
    pass


class StorageLocationUpdate(BaseModel):
    name: str | None = Field(
        None, min_length=1, max_length=100, description="Storage location name"
    )
    description: str | None = Field(
        None, max_length=500, description="Optional description"
    )
    type: StorageLocationType | None = Field(None, description="Storage location type")
    parent_id: str | None = Field(None, description="Parent storage location ID")
    qr_code_id: str | None = Field(
        None, max_length=50, description="QR code identifier"
    )

    @field_validator("parent_id")
    @classmethod
    def validate_parent_id(cls, v):  # noqa: N805
        """Validate parent_id is a valid UUID if provided."""
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError("parent_id must be a valid UUID")
        return v

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):  # noqa: N805
        """Ensure name is not empty after stripping whitespace."""
        if v is not None:
            if not v or not v.strip():
                raise ValueError("name cannot be empty")
            return v.strip()
        return v


class StorageLocationResponse(StorageLocationBase):
    id: str
    location_hierarchy: str
    created_at: str
    updated_at: str
    children: list[dict] | None = None
    component_count: int | None = None
    full_hierarchy_path: list[dict] | None = None

    class Config:
        from_attributes = True


class BulkCreateLocation(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Storage location name"
    )
    description: str | None = Field(
        None, max_length=500, description="Optional description"
    )
    type: StorageLocationType = Field(..., description="Storage location type")
    parent_name: str | None = Field(
        None, description="Reference parent by name instead of ID"
    )
    qr_code_id: str | None = Field(
        None, max_length=50, description="QR code identifier"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):  # noqa: N805
        """Ensure name is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()


class BulkCreateRequest(BaseModel):
    locations: list[BulkCreateLocation]


router = APIRouter(prefix="/api/v1/storage-locations", tags=["storage"])

# Authentication implemented - using real auth system


@router.get("", response_model=list[StorageLocationResponse])
def list_storage_locations(
    search: str | None = Query(None, description="Search in name or hierarchy"),
    type: StorageLocationType | None = Query(
        None, description="Filter by location type"
    ),
    include_component_count: bool = Query(
        False, description="Include component counts"
    ),
    limit: int = Query(100, ge=1, le=200, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db),
):
    """List storage locations with filtering and pagination."""

    service = StorageLocationService(db)
    locations = service.list_storage_locations(
        search=search,
        location_type=type.value if type else None,
        include_component_count=include_component_count,
        limit=limit,
        offset=offset,
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
            "updated_at": location.updated_at.isoformat(),
        }

        if include_component_count:
            location_dict["component_count"] = getattr(location, "component_count", 0)

        result.append(location_dict)

    return result


@router.post(
    "", response_model=StorageLocationResponse, status_code=status.HTTP_201_CREATED
)
def create_storage_location(
    location: StorageLocationCreate,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Create a new storage location."""

    service = StorageLocationService(db)

    try:
        # Convert enum to string value for service layer
        location_data = location.model_dump()
        location_data["type"] = location.type.value
        created_location = service.create_storage_location(location_data)
        return {
            "id": created_location.id,
            "name": created_location.name,
            "description": created_location.description,
            "type": created_location.type,
            "parent_id": created_location.parent_id,
            "location_hierarchy": created_location.location_hierarchy,
            "qr_code_id": created_location.qr_code_id,
            "created_at": created_location.created_at.isoformat(),
            "updated_at": created_location.updated_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Handle database constraint violations
        if "ck_storage_location_type_valid" in str(e):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid storage location type. Must be one of: {', '.join([t.value for t in StorageLocationType])}",
            )
        elif "UNIQUE constraint failed" in str(e):
            if "name" in str(e):
                raise HTTPException(
                    status_code=409, detail="Storage location name already exists"
                )
            elif "qr_code_id" in str(e):
                raise HTTPException(status_code=409, detail="QR code ID already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/bulk-create",
    response_model=list[StorageLocationResponse],
    status_code=status.HTTP_201_CREATED,
)
def bulk_create_storage_locations(
    request: BulkCreateRequest,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Bulk create storage locations with hierarchy support."""
    if not request.locations:
        raise HTTPException(status_code=422, detail="No locations provided")

    service = StorageLocationService(db)

    try:
        # Convert enum values to strings for service layer
        locations_data = []
        for loc in request.locations:
            loc_data = loc.model_dump()
            loc_data["type"] = loc.type.value
            locations_data.append(loc_data)

        created_locations = service.bulk_create_locations(locations_data)

        # Convert to response format
        result = []
        for location in created_locations:
            location_dict = {
                "id": location.id,
                "name": location.name,
                "description": location.description,
                "type": location.type,
                "parent_id": location.parent_id,
                "location_hierarchy": location.location_hierarchy,
                "qr_code_id": location.qr_code_id,
                "created_at": location.created_at.isoformat(),
                "updated_at": location.updated_at.isoformat(),
            }
            result.append(location_dict)

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Handle database constraint violations
        if "ck_storage_location_type_valid" in str(e):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid storage location type. Must be one of: {', '.join([t.value for t in StorageLocationType])}",
            )
        elif "UNIQUE constraint failed" in str(e):
            if "name" in str(e):
                raise HTTPException(
                    status_code=409, detail="Duplicate storage location name in request"
                )
            elif "qr_code_id" in str(e):
                raise HTTPException(
                    status_code=409, detail="Duplicate QR code ID in request"
                )
        raise HTTPException(status_code=400, detail="Database constraint violation")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{location_id}", response_model=StorageLocationResponse)
def get_storage_location(
    location_id: str,
    include_children: bool = Query(False, description="Include child locations"),
    include_component_count: bool = Query(False, description="Include component count"),
    include_full_hierarchy: bool = Query(
        False, description="Include full hierarchy path"
    ),
    db: Session = Depends(get_db),
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
        include_full_hierarchy=include_full_hierarchy,
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
        "updated_at": location.updated_at.isoformat(),
    }

    if include_children and hasattr(location, "children"):
        result["children"] = [
            {
                "id": child.id,
                "name": child.name,
                "type": child.type,
                "parent_id": child.parent_id,
            }
            for child in location.children
        ]

    if include_component_count:
        result["component_count"] = getattr(location, "component_count", 0)

    if include_full_hierarchy:
        result["full_hierarchy_path"] = getattr(location, "full_hierarchy_path", [])

    return result


@router.put("/{location_id}", response_model=StorageLocationResponse)
def update_storage_location(
    location_id: str,
    location_update: StorageLocationUpdate,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db),
):
    """Update a storage location."""
    try:
        uuid.UUID(location_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid location ID format")

    # Filter out None values and convert enum to string
    update_data = {}
    for k, v in location_update.model_dump().items():
        if v is not None:
            if k == "type" and isinstance(v, StorageLocationType):
                update_data[k] = v.value
            else:
                update_data[k] = v

    if not update_data:
        raise HTTPException(status_code=422, detail="No data provided for update")

    # Prevent self-reference if parent_id is being updated
    if "parent_id" in update_data and update_data["parent_id"] == location_id:
        raise HTTPException(status_code=422, detail="Location cannot be its own parent")

    service = StorageLocationService(db)

    try:
        updated_location = service.update_storage_location(location_id, update_data)
        if not updated_location:
            raise HTTPException(status_code=404, detail="Storage location not found")

        # Convert to response format
        return {
            "id": updated_location.id,
            "name": updated_location.name,
            "description": updated_location.description,
            "type": updated_location.type,
            "parent_id": updated_location.parent_id,
            "location_hierarchy": updated_location.location_hierarchy,
            "qr_code_id": updated_location.qr_code_id,
            "created_at": updated_location.created_at.isoformat(),
            "updated_at": updated_location.updated_at.isoformat(),
        }
    except HTTPException:
        # Re-raise HTTPExceptions as-is
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except IntegrityError as e:
        # Handle database constraint violations
        if "ck_storage_location_type_valid" in str(e):
            raise HTTPException(
                status_code=422,
                detail=f"Invalid storage location type. Must be one of: {', '.join([t.value for t in StorageLocationType])}",
            )
        elif "UNIQUE constraint failed" in str(e):
            if "name" in str(e):
                raise HTTPException(
                    status_code=409, detail="Storage location name already exists"
                )
            elif "qr_code_id" in str(e):
                raise HTTPException(status_code=409, detail="QR code ID already exists")
        raise HTTPException(status_code=400, detail="Database constraint violation")
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{location_id}/components")
def get_location_components(
    location_id: str,
    include_children: bool = Query(
        False, description="Include components from child locations"
    ),
    search: str | None = Query(None, description="Search in component names"),
    category: str | None = Query(None, description="Filter by category"),
    component_type: str | None = Query(None, description="Filter by component type"),
    stock_status: str | None = Query(
        None, pattern="^(low|out|available)$", description="Filter by stock status"
    ),
    sort_by: str = Query("name", pattern="^(name|quantity)$", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    limit: int = Query(50, ge=1, le=100, description="Number of components to return"),
    offset: int = Query(0, ge=0, description="Number of components to skip"),
    db: Session = Depends(get_db),
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
        offset=offset,
    )

    # Convert to response format (similar to components API)
    result = []
    for component in components:
        # Get the ComponentLocation record for this specific location
        from ..models import ComponentLocation

        component_location = (
            db.query(ComponentLocation)
            .filter(
                ComponentLocation.component_id == component.id,
                ComponentLocation.storage_location_id == location_id,
            )
            .first()
        )

        # Use location-specific quantities if available, otherwise use component totals
        location_quantity = (
            component_location.quantity_on_hand if component_location else 0
        )
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
                "location_hierarchy": component.primary_location.location_hierarchy,
            }
            if component.primary_location
            else None,
            "category": {"id": component.category.id, "name": component.category.name}
            if component.category
            else None,
        }
        result.append(component_dict)

    return result
