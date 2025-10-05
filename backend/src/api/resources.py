"""
Resource API endpoints for managing provider-linked resource downloads.

Provides endpoints for checking download status and adding new resources
to provider links.
"""

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth.dependencies import require_admin
from ..database import get_db
from ..services.resource_service import ResourceService

router = APIRouter(prefix="/api", tags=["resources"])


# Pydantic schemas
class ResourceStatusResponse(BaseModel):
    """Resource download status response"""

    id: int
    download_status: str
    progress_percent: int
    error_message: str | None = None
    file_size_bytes: int | None = None
    downloaded_at: str | None = None


class AddResourceRequest(BaseModel):
    """Request schema for adding a resource"""

    type: Literal["datasheet", "image", "footprint", "symbol", "model_3d"]
    url: str
    file_name: str


class ResourceResponse(BaseModel):
    """Resource response schema"""

    id: int
    resource_type: str
    file_name: str
    source_url: str
    download_status: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("/resources/{resource_id}/status", response_model=ResourceStatusResponse)
async def get_resource_status(
    resource_id: int,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get download status for a resource.

    Returns current download status, progress, and error information.
    Used for polling resource download progress during wizard workflow.

    Args:
        resource_id: Resource ID

    Returns:
        ResourceStatusResponse with status and progress information

    Raises:
        404: Resource not found

    Requires: Admin authentication
    """
    try:
        status_data = await ResourceService.get_resource_status(db, resource_id)

        return ResourceStatusResponse(**status_data)

    except ValueError as e:
        # Resource not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resource status: {str(e)}",
        )


@router.post(
    "/provider-links/{link_id}/resources",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_resource(
    link_id: int,
    resource_data: AddResourceRequest,
    background_tasks: BackgroundTasks,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Add a new resource to a provider link.

    Creates a resource record and queues it for background download.
    Used for adding additional resources after initial component creation.

    Args:
        link_id: Provider link ID
        resource_data: Resource data (type, url, file_name)
        background_tasks: FastAPI background tasks

    Returns:
        Created Resource

    Raises:
        404: Provider link not found
        400: Validation error (invalid type, etc.)

    Requires: Admin authentication
    """
    try:
        # Convert Pydantic model to dict
        data = resource_data.model_dump()

        # Add resource via service
        resource = await ResourceService.add_resource(
            db, link_id, data, background_tasks=background_tasks
        )

        # Return resource response
        return {
            "id": resource.id,
            "resource_type": resource.resource_type,
            "file_name": resource.file_name,
            "source_url": resource.source_url,
            "download_status": resource.download_status,
            "created_at": resource.created_at.isoformat()
            if resource.created_at
            else None,
        }

    except ValueError as e:
        # Validation error or provider link not found
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    except Exception as e:
        # Creation failed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add resource: {str(e)}",
        )
