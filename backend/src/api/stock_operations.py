"""
Stock operations API endpoints for component stock management.

Provides three atomic stock operations:
- POST /api/v1/components/{component_id}/stock/add - Add stock to location
- POST /api/v1/components/{component_id}/stock/remove - Remove stock from location
- POST /api/v1/components/{component_id}/stock/move - Move stock between locations

All endpoints require admin authentication and support pessimistic locking,
auto-capping, and full audit trails via StockTransaction records.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..auth.dependencies import require_admin
from ..database import get_db
from ..schemas.stock_operations import (
    AddStockRequest,
    AddStockResponse,
    MoveStockRequest,
    MoveStockResponse,
    RemoveStockRequest,
    RemoveStockResponse,
)
from ..services.stock_operations import StockOperationsService

router = APIRouter(prefix="/api/v1/components", tags=["Stock Operations"])


@router.post(
    "/{component_id}/stock/add",
    response_model=AddStockResponse,
    status_code=status.HTTP_200_OK,
)
async def add_stock(
    component_id: UUID,
    request: AddStockRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> AddStockResponse:
    """
    Add stock to a component at a specific location.

    Admin-only operation that:
    - Creates or updates ComponentLocation entry
    - Records StockTransaction for audit trail
    - Supports per-unit or total pricing
    - Uses pessimistic locking to prevent race conditions

    Args:
        component_id: UUID of component to add stock to
        request: Add stock request with location, quantity, and optional pricing
        db: Database session (injected)
        admin: Current admin user (injected)

    Returns:
        AddStockResponse with transaction details and updated quantities

    Raises:
        HTTPException 400: Invalid input data (validation errors)
        HTTPException 403: User is not admin
        HTTPException 404: Component or location not found
        HTTPException 409: Concurrent modification (lock timeout)
    """
    service = StockOperationsService(db)
    result = service.add_stock(
        component_id=str(component_id),
        location_id=str(request.location_id),
        quantity=request.quantity,
        user=admin,
        price_per_unit=request.price_per_unit,
        total_price=request.total_price,
        lot_id=request.lot_id,
        comments=request.comments,
        reference_id=request.reference_id,
        reference_type=request.reference_type,
    )
    return AddStockResponse(**result)


@router.post(
    "/{component_id}/stock/remove",
    response_model=RemoveStockResponse,
    status_code=status.HTTP_200_OK,
)
async def remove_stock(
    component_id: UUID,
    request: RemoveStockRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> RemoveStockResponse:
    """
    Remove stock from a component at a specific location.

    Admin-only operation that:
    - Updates ComponentLocation quantity (or deletes if zero)
    - Records StockTransaction for audit trail
    - Auto-caps removal at available stock (no over-removal)
    - Uses pessimistic locking to prevent race conditions

    Args:
        component_id: UUID of component to remove stock from
        request: Remove stock request with location, quantity, and reason
        db: Database session (injected)
        admin: Current admin user (injected)

    Returns:
        RemoveStockResponse with capping status and updated quantities

    Raises:
        HTTPException 400: Invalid input data (validation errors)
        HTTPException 403: User is not admin
        HTTPException 404: Component or ComponentLocation not found
        HTTPException 409: Concurrent modification (lock timeout)
    """
    service = StockOperationsService(db)
    result = service.remove_stock(
        component_id=str(component_id),
        location_id=str(request.location_id),
        quantity=request.quantity,
        user=admin,
        comments=request.comments,
        reason=request.reason,
    )
    return RemoveStockResponse(**result)


@router.post(
    "/{component_id}/stock/move",
    response_model=MoveStockResponse,
    status_code=status.HTTP_200_OK,
)
async def move_stock(
    component_id: UUID,
    request: MoveStockRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> MoveStockResponse:
    """
    Move stock between two storage locations atomically.

    Admin-only operation that:
    - Decrements source location quantity (deletes if zero)
    - Increments destination location quantity (creates if needed)
    - Records TWO StockTransactions (REMOVE + ADD) for audit trail
    - Auto-caps move at available source stock
    - Inherits pricing from source to destination if destination is new
    - Uses pessimistic locking on BOTH locations to prevent race conditions

    Args:
        component_id: UUID of component to move stock for
        request: Move stock request with source, destination, and quantity
        db: Database session (injected)
        admin: Current admin user (injected)

    Returns:
        MoveStockResponse with source/destination states and pricing inheritance

    Raises:
        HTTPException 400: Invalid input data (source == destination)
        HTTPException 403: User is not admin
        HTTPException 404: Component or source location not found
        HTTPException 409: Concurrent modification (lock timeout)
    """
    service = StockOperationsService(db)
    result = service.move_stock(
        component_id=str(component_id),
        source_location_id=str(request.source_location_id),
        destination_location_id=str(request.destination_location_id),
        quantity=request.quantity,
        user=admin,
        comments=request.comments,
    )
    return MoveStockResponse(**result)
