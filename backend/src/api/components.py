"""
Components API endpoints implementing the OpenAPI specification.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import uuid
import math

from ..database import get_db
from ..services.component_service import ComponentService
from ..models import Component, StockTransaction
from ..auth.dependencies import require_auth, get_optional_user

# Pydantic schemas
class ComponentBase(BaseModel):
    name: str
    part_number: Optional[str] = None  # Legacy field maintained for backward compatibility
    local_part_id: Optional[str] = None  # User-friendly local identifier
    barcode_id: Optional[str] = None  # Auto-generated barcode/QR code ID
    manufacturer_part_number: Optional[str] = None  # Official manufacturer part number
    provider_sku: Optional[str] = None  # Provider-specific SKU
    manufacturer: Optional[str] = None
    category_id: Optional[str] = None
    storage_location_id: Optional[str] = None
    component_type: Optional[str] = None
    value: Optional[str] = None
    package: Optional[str] = None
    quantity_on_hand: int = 0
    quantity_ordered: int = 0
    minimum_stock: int = 0
    average_purchase_price: Optional[float] = None
    total_purchase_value: Optional[float] = None
    notes: Optional[str] = None
    specifications: Optional[dict] = None
    custom_fields: Optional[dict] = None
    tags: Optional[List[str]] = None  # List of tag IDs

class ComponentCreate(ComponentBase):
    pass

class ComponentUpdate(BaseModel):
    name: Optional[str] = None
    part_number: Optional[str] = None  # Legacy field maintained for backward compatibility
    local_part_id: Optional[str] = None  # User-friendly local identifier
    barcode_id: Optional[str] = None  # Auto-generated barcode/QR code ID
    manufacturer_part_number: Optional[str] = None  # Official manufacturer part number
    provider_sku: Optional[str] = None  # Provider-specific SKU
    manufacturer: Optional[str] = None
    category_id: Optional[str] = None
    storage_location_id: Optional[str] = None
    component_type: Optional[str] = None
    value: Optional[str] = None
    package: Optional[str] = None
    minimum_stock: Optional[int] = None
    notes: Optional[str] = None
    specifications: Optional[dict] = None

class ComponentResponse(ComponentBase):
    id: str
    category: Optional[dict] = None
    storage_location: Optional[dict] = None
    storage_locations: List[dict] = []
    tags: List[dict] = []
    attachments: List[dict] = []
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True

class StockTransactionCreate(BaseModel):
    transaction_type: str = Field(..., pattern="^(add|remove|move|adjust)$")
    quantity_change: int
    reason: str
    reference_id: Optional[str] = None

class StockTransactionResponse(BaseModel):
    id: str
    component_id: str
    transaction_type: str
    quantity_change: int
    previous_quantity: int
    new_quantity: int
    reason: str
    reference_id: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True

class ComponentsListResponse(BaseModel):
    components: List[ComponentResponse]
    total: int
    page: int
    total_pages: int
    limit: int

router = APIRouter(prefix="/api/v1/components", tags=["components"])

# Authentication implemented - using real auth system

@router.get("", response_model=ComponentsListResponse)
def list_components(
    search: Optional[str] = Query(None, description="Search in name, part number, manufacturer"),
    category: Optional[str] = Query(None, description="Filter by category name"),
    storage_location: Optional[str] = Query(None, description="Filter by storage location"),
    component_type: Optional[str] = Query(None, description="Filter by component type"),
    stock_status: Optional[str] = Query(None, pattern="^(low|out|available)$", description="Filter by stock status"),
    sort_by: str = Query("name", pattern="^(name|quantity|created_at)$", description="Sort field"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$", description="Sort order"),
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    db: Session = Depends(get_db)
):
    """List components with filtering and pagination."""
    service = ComponentService(db)

    # Get total count for pagination
    total_count = service.count_components(
        search=search,
        category=category,
        storage_location=storage_location,
        component_type=component_type,
        stock_status=stock_status
    )

    components = service.list_components(
        search=search,
        category=category,
        storage_location=storage_location,
        component_type=component_type,
        stock_status=stock_status,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )

    # Convert to response format
    component_list = []
    for component in components:
        component_dict = {
            "id": component.id,
            "name": component.name,
            "part_number": component.part_number,
            "local_part_id": component.local_part_id,
            "barcode_id": component.barcode_id,
            "manufacturer_part_number": component.manufacturer_part_number,
            "provider_sku": component.provider_sku,
            "manufacturer": component.manufacturer,
            "category_id": component.category_id,
            "storage_location_id": component.storage_locations[0].id if component.storage_locations else None,
            "component_type": component.component_type,
            "value": component.value,
            "package": component.package,
            "quantity_on_hand": component.quantity_on_hand,
            "quantity_ordered": component.quantity_ordered,
            "minimum_stock": component.minimum_stock,
            "average_purchase_price": float(component.average_purchase_price) if component.average_purchase_price else None,
            "total_purchase_value": float(component.total_purchase_value) if component.total_purchase_value else None,
            "notes": component.notes,
            "specifications": component.specifications,
            "custom_fields": component.custom_fields,
            "category": {"id": component.category.id, "name": component.category.name} if component.category else None,
            "storage_location": {
                "id": component.primary_location.id,
                "name": component.primary_location.name,
                "location_hierarchy": component.primary_location.location_hierarchy
            } if component.primary_location else None,
            "storage_locations": [
                {
                    "location": {
                        "id": loc.storage_location.id,
                        "name": loc.storage_location.name,
                        "location_hierarchy": loc.storage_location.location_hierarchy
                    },
                    "quantity_on_hand": loc.quantity_on_hand,
                    "quantity_ordered": loc.quantity_ordered,
                    "minimum_stock": loc.minimum_stock,
                    "location_notes": loc.location_notes,
                    "unit_cost_at_location": float(loc.unit_cost_at_location) if loc.unit_cost_at_location else None
                }
                for loc in component.locations
            ],
            "tags": [{"id": tag.id, "name": tag.name} for tag in component.tags],
            "attachments": [{"id": att.id, "filename": att.filename} for att in component.attachments],
            "created_at": component.created_at.isoformat(),
            "updated_at": component.updated_at.isoformat()
        }
        component_list.append(component_dict)

    # Calculate pagination info
    page = (offset // limit) + 1
    total_pages = math.ceil(total_count / limit) if limit > 0 else 1

    return ComponentsListResponse(
        components=component_list,
        total=total_count,
        page=page,
        total_pages=total_pages,
        limit=limit
    )

@router.post("", response_model=ComponentResponse, status_code=status.HTTP_201_CREATED)
def create_component(
    component: ComponentCreate,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Create a new component."""
    service = ComponentService(db)

    try:
        # Validate UUID fields if provided
        if component.category_id:
            uuid.UUID(component.category_id)
        if component.storage_location_id:
            uuid.UUID(component.storage_location_id)

        created_component = service.create_component(component.model_dump())

        # Format the response properly
        return {
            "id": created_component.id,
            "name": created_component.name,
            "part_number": created_component.part_number,
            "local_part_id": created_component.local_part_id,
            "barcode_id": created_component.barcode_id,
            "manufacturer_part_number": created_component.manufacturer_part_number,
            "provider_sku": created_component.provider_sku,
            "manufacturer": created_component.manufacturer,
            "category_id": created_component.category_id,
            "storage_location_id": created_component.storage_locations[0].id if created_component.storage_locations else None,
            "component_type": created_component.component_type,
            "value": created_component.value,
            "package": created_component.package,
            "quantity_on_hand": created_component.quantity_on_hand,
            "quantity_ordered": created_component.quantity_ordered,
            "minimum_stock": created_component.minimum_stock,
            "average_purchase_price": float(created_component.average_purchase_price) if created_component.average_purchase_price else None,
            "total_purchase_value": float(created_component.total_purchase_value) if created_component.total_purchase_value else None,
            "notes": created_component.notes,
            "specifications": created_component.specifications,
            "custom_fields": created_component.custom_fields,
            "category": {"id": created_component.category.id, "name": created_component.category.name} if created_component.category else None,
            "storage_location": {
                "id": created_component.primary_location.id,
                "name": created_component.primary_location.name,
                "location_hierarchy": created_component.primary_location.location_hierarchy
            } if created_component.primary_location else None,
            "tags": [{"id": tag.id, "name": tag.name} for tag in created_component.tags],
            "attachments": [{"id": att.id, "filename": att.filename} for att in created_component.attachments],
            "created_at": created_component.created_at.isoformat(),
            "updated_at": created_component.updated_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{component_id}", response_model=ComponentResponse)
def get_component(
    component_id: str,
    db: Session = Depends(get_db)
):
    """Get a component by ID."""
    try:
        uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid component ID format")

    service = ComponentService(db)
    component = service.get_component(component_id)

    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    return {
        "id": component.id,
        "name": component.name,
        "part_number": component.part_number,
        "local_part_id": component.local_part_id,
        "barcode_id": component.barcode_id,
        "manufacturer_part_number": component.manufacturer_part_number,
        "provider_sku": component.provider_sku,
        "manufacturer": component.manufacturer,
        "category_id": component.category_id,
        "storage_location_id": component.storage_locations[0].id if component.storage_locations else None,
        "component_type": component.component_type,
        "value": component.value,
        "package": component.package,
        "quantity_on_hand": component.quantity_on_hand,
        "quantity_ordered": component.quantity_ordered,
        "minimum_stock": component.minimum_stock,
        "average_purchase_price": component.average_purchase_price,
        "total_purchase_value": component.total_purchase_value,
        "notes": component.notes,
        "specifications": component.specifications,
        "custom_fields": component.custom_fields,
        "category": {"id": component.category.id, "name": component.category.name} if component.category else None,
        "storage_location": {
            "id": component.primary_location.id,
            "name": component.primary_location.name,
            "location_hierarchy": component.primary_location.location_hierarchy
        } if component.primary_location else None,
        "storage_locations": [
            {
                "location": {
                    "id": loc.storage_location.id,
                    "name": loc.storage_location.name,
                    "location_hierarchy": loc.storage_location.location_hierarchy
                },
                "quantity_on_hand": loc.quantity_on_hand,
                "quantity_ordered": loc.quantity_ordered,
                "minimum_stock": loc.minimum_stock,
                "location_notes": loc.location_notes,
                "unit_cost_at_location": float(loc.unit_cost_at_location) if loc.unit_cost_at_location else None
            }
            for loc in component.locations
        ],
        "tags": [{"id": tag.id, "name": tag.name} for tag in component.tags],
        "attachments": [{"id": att.id, "filename": att.filename} for att in component.attachments],
        "created_at": component.created_at.isoformat() if component.created_at else "",
        "updated_at": component.updated_at.isoformat() if component.updated_at else ""
    }

@router.put("/{component_id}", response_model=ComponentResponse)
def update_component(
    component_id: str,
    component_update: ComponentUpdate,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update a component."""
    try:
        uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid component ID format")

    service = ComponentService(db)

    # Filter out None values
    update_data = {k: v for k, v in component_update.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=422, detail="No data provided for update")

    try:
        updated_component = service.update_component(component_id, update_data)
        if not updated_component:
            raise HTTPException(status_code=404, detail="Component not found")
        return updated_component
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

@router.delete("/{component_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_component(
    component_id: str,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Delete a component."""
    try:
        uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid component ID format")

    service = ComponentService(db)
    success = service.delete_component(component_id)

    if not success:
        raise HTTPException(status_code=404, detail="Component not found")

@router.post("/{component_id}/stock", response_model=StockTransactionResponse)
def update_component_stock(
    component_id: str,
    stock_update: StockTransactionCreate,
    current_user=Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Update component stock."""
    try:
        uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid component ID format")

    service = ComponentService(db)

    try:
        transaction = service.update_stock(
            component_id=component_id,
            transaction_type=stock_update.transaction_type,
            quantity_change=stock_update.quantity_change,
            reason=stock_update.reason,
            reference_id=stock_update.reference_id,
            reference_type="api_update"
        )

        if not transaction:
            raise HTTPException(status_code=404, detail="Component not found")

        return transaction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{component_id}/history", response_model=List[StockTransactionResponse])
def get_component_history(
    component_id: str,
    limit: int = Query(50, ge=1, le=100, description="Number of transactions to return"),
    db: Session = Depends(get_db)
):
    """Get component stock transaction history."""
    try:
        uuid.UUID(component_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid component ID format")

    service = ComponentService(db)

    # Verify component exists
    component = service.get_component(component_id)
    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    transactions = service.get_stock_history(component_id, limit)
    return transactions