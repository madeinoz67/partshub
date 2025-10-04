"""
Bulk operations API endpoints for components.

Provides endpoints for bulk operations on components including:
- Tag addition/removal
- Project assignment
- Component deletion
- Other bulk operations (meta-parts, purchase lists, low stock, attribution)

All endpoints require admin authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from ..auth.dependencies import require_admin
from ..database import get_db
from ..models.component import Component
from ..schemas.bulk_operations import (
    BulkAddTagsRequest,
    BulkAssignProjectRequest,
    BulkAttributionRequest,
    BulkDeleteRequest,
    BulkLowStockRequest,
    BulkMetaPartRequest,
    BulkOperationResponse,
    BulkPurchaseListRequest,
    BulkRemoveTagsRequest,
    ComponentTagPreview,
    TagPreviewResponse,
)
from ..services.bulk_operation_service import BulkOperationService

router = APIRouter(prefix="/api/v1/components/bulk", tags=["Bulk Operations"])


@router.post(
    "/tags/add",
    response_model=BulkOperationResponse,
    status_code=status.HTTP_200_OK,
)
async def bulk_add_tags(
    request: BulkAddTagsRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> BulkOperationResponse:
    """
    Add tags to multiple components atomically.

    Requires admin authentication. Creates new Tag records if they don't exist.
    All operations succeed or all are rolled back.

    Args:
        request: Bulk add tags request with component IDs and tag names
        db: Database session
        admin: Current admin user

    Returns:
        BulkOperationResponse with success status and affected count
    """
    service = BulkOperationService(db)
    return await service.bulk_add_tags(request.component_ids, request.tags)


@router.post(
    "/tags/remove",
    response_model=BulkOperationResponse,
    status_code=status.HTTP_200_OK,
)
async def bulk_remove_tags(
    request: BulkRemoveTagsRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> BulkOperationResponse:
    """
    Remove tags from multiple components atomically.

    Requires admin authentication. All operations succeed or all are rolled back.

    Args:
        request: Bulk remove tags request with component IDs and tag names
        db: Database session
        admin: Current admin user

    Returns:
        BulkOperationResponse with success status and affected count
    """
    service = BulkOperationService(db)
    return await service.bulk_remove_tags(request.component_ids, request.tags)


@router.get(
    "/tags/preview",
    response_model=TagPreviewResponse,
    status_code=status.HTTP_200_OK,
)
async def bulk_tags_preview(
    component_ids: str,
    tags_to_add: str = "",
    tags_to_remove: str = "",
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> TagPreviewResponse:
    """
    Preview the result of bulk tag operations without making changes.

    Requires admin authentication. Calculates and returns the resulting tags
    for each component after applying the specified add/remove operations.

    Args:
        component_ids: Comma-separated list of component IDs
        tags_to_add: Comma-separated list of tags to add
        tags_to_remove: Comma-separated list of tags to remove
        db: Database session
        admin: Current admin user

    Returns:
        TagPreviewResponse with preview of each component's tags
    """
    # Parse comma-separated strings
    comp_ids = [id.strip() for id in component_ids.split(",") if id.strip()]
    add_tags = [tag.strip() for tag in tags_to_add.split(",") if tag.strip()]
    remove_tags = [tag.strip() for tag in tags_to_remove.split(",") if tag.strip()]

    # Fetch components with tags
    components = (
        db.query(Component)
        .options(selectinload(Component.tags))
        .filter(Component.id.in_(comp_ids))
        .all()
    )

    # Calculate preview for each component
    previews = []
    for component in components:
        current_tags = {t.name for t in component.tags}
        resulting_tags = current_tags.copy()

        # Apply add operation
        for tag in add_tags:
            resulting_tags.add(tag)

        # Apply remove operation
        for tag in remove_tags:
            resulting_tags.discard(tag)

        previews.append(
            ComponentTagPreview(
                component_id=component.id,
                component_name=component.name,
                current_tags=sorted(current_tags),
                resulting_tags=sorted(resulting_tags),
            )
        )

    return TagPreviewResponse(components=previews)


@router.post(
    "/projects/assign",
    response_model=BulkOperationResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Project not found"},
    },
)
async def bulk_assign_project(
    request: BulkAssignProjectRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> BulkOperationResponse:
    """
    Assign multiple components to a project atomically.

    Requires admin authentication. Creates or updates ProjectComponent records.
    All operations succeed or all are rolled back.

    Args:
        request: Bulk assign project request with component IDs, project ID, and quantities
        db: Database session
        admin: Current admin user

    Returns:
        BulkOperationResponse with success status and affected count

    Raises:
        HTTPException: 404 if project not found
    """
    service = BulkOperationService(db)
    result = await service.bulk_assign_project(
        request.component_ids, request.project_id, request.quantities
    )

    # Check if project not found (return 404 per OpenAPI spec)
    if not result.success and result.errors:
        for error in result.errors:
            if "Project" in error.error_message and "not found" in error.error_message:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=error.error_message,
                )

    return result


@router.post(
    "/delete",
    response_model=BulkOperationResponse,
    status_code=status.HTTP_200_OK,
)
async def bulk_delete(
    request: BulkDeleteRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> BulkOperationResponse:
    """
    Delete multiple components atomically.

    Requires admin authentication. All deletions succeed or all are rolled back.

    Args:
        request: Bulk delete request with component IDs
        db: Database session
        admin: Current admin user

    Returns:
        BulkOperationResponse with success status and affected count
    """
    service = BulkOperationService(db)
    return await service.bulk_delete(request.component_ids)


# Stub implementations for future features
@router.post(
    "/meta-parts/add",
    response_model=BulkOperationResponse,
    status_code=status.HTTP_200_OK,
)
async def bulk_add_meta_parts(
    request: BulkMetaPartRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> BulkOperationResponse:
    """
    Add components to a meta-part atomically (stub implementation).

    Requires admin authentication.

    Args:
        request: Bulk meta-part request
        db: Database session
        admin: Current admin user

    Returns:
        BulkOperationResponse (stub - always succeeds)
    """
    # Stub implementation - return success
    return BulkOperationResponse(
        success=True, affected_count=len(request.component_ids), errors=None
    )


@router.post(
    "/purchase-lists/add",
    response_model=BulkOperationResponse,
    status_code=status.HTTP_200_OK,
)
async def bulk_add_to_purchase_list(
    request: BulkPurchaseListRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> BulkOperationResponse:
    """
    Add components to a purchase list atomically (stub implementation).

    Requires admin authentication.

    Args:
        request: Bulk purchase list request
        db: Database session
        admin: Current admin user

    Returns:
        BulkOperationResponse (stub - always succeeds)
    """
    # Stub implementation - return success
    return BulkOperationResponse(
        success=True, affected_count=len(request.component_ids), errors=None
    )


@router.post(
    "/low-stock/set",
    response_model=BulkOperationResponse,
    status_code=status.HTTP_200_OK,
)
async def bulk_set_low_stock(
    request: BulkLowStockRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> BulkOperationResponse:
    """
    Set low stock threshold for multiple components atomically (stub implementation).

    Requires admin authentication.

    Args:
        request: Bulk low stock request
        db: Database session
        admin: Current admin user

    Returns:
        BulkOperationResponse (stub - always succeeds)
    """
    # Stub implementation - return success
    return BulkOperationResponse(
        success=True, affected_count=len(request.component_ids), errors=None
    )


@router.post(
    "/attribution/set",
    response_model=BulkOperationResponse,
    status_code=status.HTTP_200_OK,
)
async def bulk_set_attribution(
    request: BulkAttributionRequest,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> BulkOperationResponse:
    """
    Set attribution metadata for multiple components atomically (stub implementation).

    Requires admin authentication.

    Args:
        request: Bulk attribution request
        db: Database session
        admin: Current admin user

    Returns:
        BulkOperationResponse (stub - always succeeds)
    """
    # Stub implementation - return success
    return BulkOperationResponse(
        success=True, affected_count=len(request.component_ids), errors=None
    )
