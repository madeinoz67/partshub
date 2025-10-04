"""
Storage Location Layout Generator API endpoints.

Implements the OpenAPI specification for bulk location generation with
preview and creation endpoints.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..auth.dependencies import require_auth
from ..database import get_db
from ..schemas.location_layout import (
    BulkCreateResponse,
    LayoutConfiguration,
    PreviewResponse,
)
from ..services.bulk_create_service import BulkCreateService
from ..services.preview_service import PreviewService

router = APIRouter(prefix="/api/v1/storage-locations", tags=["Storage Locations"])


@router.post(
    "/generate-preview",
    response_model=PreviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Preview generated storage location names",
    description="""
Generate a preview of storage locations that would be created based on layout configuration.
Returns first 5 names, last name, total count, and validation errors. No locations are created.
This endpoint is idempotent and has no side effects.
    """,
)
def generate_preview(
    config: LayoutConfiguration,
    db: Session = Depends(get_db),
) -> PreviewResponse:
    """
    Preview storage location names before creation.

    FR-005: System MUST provide real-time preview showing generated location names.
    FR-013: System MUST display preview showing first 5 generated names, ellipsis, last name, and total count.

    Args:
        config: Layout configuration with layout type, ranges, and separators
        db: Database session

    Returns:
        PreviewResponse with sample names, total count, warnings, and errors

    No authentication required - preview is read-only and has no side effects.
    """
    preview_service = PreviewService(db)
    return preview_service.generate_preview(config)


@router.post(
    "/bulk-create-layout",
    response_model=BulkCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create storage locations from layout",
    description="""
Create multiple storage locations based on layout configuration.
All locations are created in a single transaction (all-or-nothing).
Requires authentication. Maximum 500 locations per request.
    """,
    responses={
        201: {"description": "Locations created successfully"},
        400: {
            "description": "Validation error (exceeds limit)",
            "model": BulkCreateResponse,
        },
        404: {"description": "Parent location not found", "model": BulkCreateResponse},
        409: {"description": "Duplicate location names", "model": BulkCreateResponse},
    },
)
def bulk_create_locations(
    config: LayoutConfiguration,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_auth),
):
    """
    Create storage locations in bulk based on layout configuration.

    FR-001: System MUST allow authenticated users to create storage locations.
    FR-007: System MUST prevent creation of locations with names that already exist.
    FR-008: System MUST enforce maximum limit of 500 locations per bulk creation operation.
    FR-014: System MUST allow users to assign all generated locations to an optional parent location.
    FR-015: System MUST allow users to mark generated locations as "single-part only" storage.
    FR-016: System MUST persist layout configuration with each created location for audit purposes.
    FR-021: System MUST allow users to select a location type.
    FR-022: System MUST refresh location tree immediately after successful creation.
    FR-023: System MUST show success notification with count of created locations.
    FR-024: Anonymous users MUST NOT be able to access location creation functionality.

    Args:
        config: Layout configuration with all parameters
        db: Database session
        current_user: Authenticated user from JWT token

    Returns:
        BulkCreateResponse with created location IDs and operation status
    """
    from fastapi.responses import JSONResponse

    bulk_service = BulkCreateService(db)

    # Create locations
    response = bulk_service.bulk_create_locations(
        config, user_id=current_user.get("user_id")
    )

    # If validation failed, return appropriate error status with full response
    if not response.success and response.errors:
        # Check if it's a duplicate error (FR-007)
        error_text = " ".join(response.errors).lower()
        if "duplicate" in error_text or "already exist" in error_text:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=response.model_dump(),
            )

        # Check if it's a limit error (FR-008)
        if "500" in error_text or "limit" in error_text:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=response.model_dump(),
            )

        # Check if it's a parent error (FR-014)
        if "parent" in error_text:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content=response.model_dump(),
            )

        # Generic validation error
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=response.model_dump(),
        )

    # Success - return 201 Created with response
    return response
