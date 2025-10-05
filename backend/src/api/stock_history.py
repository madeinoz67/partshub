"""
Stock history API endpoints for paginated history and multi-format exports.

Provides two endpoints:
- GET /api/v1/components/{id}/stock/history - Paginated history with sorting
- GET /api/v1/components/{id}/stock/history/export - Export to CSV/Excel/JSON

All endpoints require authentication. Export endpoint requires admin privileges.
"""

import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..auth.dependencies import require_admin, require_auth
from ..database import get_db
from ..services.stock_history_service import StockHistoryService

router = APIRouter(prefix="/api/v1/components", tags=["Stock History"])


@router.get(
    "/{component_id}/stock/history",
    status_code=status.HTTP_200_OK,
)
async def get_stock_history(
    component_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(
        10, ge=1, le=100, description="Entries per page (default 10)"
    ),
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|quantity_change|transaction_type|user_name)$",
        description="Field to sort by",
    ),
    sort_order: str = Query(
        "desc", pattern="^(asc|desc)$", description="Sort order (asc or desc)"
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_auth
    ),  # Authenticated access (NOT admin-only per FR-044)
):
    """
    Get paginated stock transaction history for a component.

    Authenticated operation (not admin-only per FR-044) that:
    - Returns paginated transaction history (10 per page by default per FR-047)
    - Supports sorting by created_at, quantity_change, transaction_type, or user_name (FR-044)
    - Includes location names and pricing information (FR-043)
    - Updates in real-time when stock operations occur (FR-045)

    Args:
        component_id: UUID of component
        page: Page number (1-indexed, default 1)
        page_size: Entries per page (default 10, max 100)
        sort_by: Field to sort by (default created_at)
        sort_order: Sort order (default desc)
        db: Database session (injected)
        current_user: Current authenticated user (injected)

    Returns:
        JSON response with:
            - entries: List of stock transaction history entries
            - pagination: Metadata (page, page_size, total_entries, total_pages, has_next, has_previous)

    Raises:
        HTTPException 401: User is not authenticated
        HTTPException 404: Component not found
        HTTPException 400: Invalid pagination or sort parameters
    """
    service = StockHistoryService(db)

    try:
        result = service.get_paginated_history(
            component_id=str(component_id),
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # Convert StockTransaction objects to dicts for JSON response
        serialized_entries = []
        for txn in result["entries"]:
            serialized_entries.append(
                {
                    "id": txn.id,
                    "created_at": txn.created_at.isoformat()
                    if txn.created_at
                    else None,
                    "transaction_type": txn.transaction_type.value.upper(),
                    "quantity_change": txn.quantity_change,
                    "previous_quantity": txn.previous_quantity,
                    "new_quantity": txn.new_quantity,
                    "from_location_id": txn.from_location_id,
                    "from_location_name": txn.from_location.name
                    if txn.from_location
                    else None,
                    "to_location_id": txn.to_location_id,
                    "to_location_name": txn.to_location.name
                    if txn.to_location
                    else None,
                    "lot_id": txn.lot_id,
                    "price_per_unit": float(txn.price_per_unit)
                    if txn.price_per_unit
                    else None,
                    "total_price": float(txn.total_price) if txn.total_price else None,
                    "user_id": txn.user_id,
                    "user_name": txn.user_name,
                    "reason": txn.reason,
                    "notes": txn.notes,
                }
            )

        return {
            "entries": serialized_entries,
            "pagination": result["pagination"],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stock history: {str(e)}",
        )


@router.get(
    "/{component_id}/stock/history/export",
    status_code=status.HTTP_200_OK,
)
async def export_stock_history(
    component_id: UUID,
    format: str = Query(
        ...,
        pattern="^(csv|xlsx|json)$",
        description="Export format (csv, xlsx, or json)",
    ),
    sort_by: str = Query(
        "created_at",
        pattern="^(created_at|quantity_change|transaction_type|user_name)$",
        description="Field to sort by",
    ),
    sort_order: str = Query(
        "desc", pattern="^(asc|desc)$", description="Sort order (asc or desc)"
    ),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),  # Admin-only access per FR-059
):
    """
    Export complete stock transaction history in specified format.

    Admin-only operation (per FR-059) that:
    - Exports ALL transaction history (no pagination)
    - Supports CSV, Excel/XLSX, and JSON formats
    - Includes proper headers and formatting per FR-043
    - Returns streaming response with appropriate content-type headers

    Args:
        component_id: UUID of component
        format: Export format (csv, xlsx, or json)
        sort_by: Field to sort by (default created_at)
        sort_order: Sort order (default desc)
        db: Database session (injected)
        admin: Current admin user (injected)

    Returns:
        StreamingResponse with:
            - CSV: text/csv content-type
            - Excel: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
            - JSON: application/json
            - Content-Disposition header with filename

    Raises:
        HTTPException 401: User is not authenticated
        HTTPException 403: User is not admin
        HTTPException 404: Component not found
        HTTPException 400: Invalid format parameter
    """
    service = StockHistoryService(db)

    try:
        result = service.export_history(
            component_id=str(component_id),
            export_format=format,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Component not found",
            )

        content, content_type, filename = result

        # Create appropriate stream based on content type
        if isinstance(content, bytes):
            # XLSX format (binary)
            stream = io.BytesIO(content)
        else:
            # CSV or JSON format (text)
            stream = io.BytesIO(content.encode("utf-8"))

        # Ensure stream is at beginning before reading
        stream.seek(0)

        return StreamingResponse(
            stream,
            media_type=content_type,
            headers={
                "Content-Type": content_type,  # Explicit header to prevent charset=utf-8 addition
                "Content-Disposition": f"attachment; filename={filename}",
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export stock history: {str(e)}",
        )
