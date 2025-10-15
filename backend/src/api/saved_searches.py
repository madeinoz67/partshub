"""
Saved Searches API endpoints for managing user's component search queries.
"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth.dependencies import require_auth
from ..database import get_db
from ..services.saved_search_service import SavedSearchService


# Pydantic schemas
class SavedSearchCreate(BaseModel):
    """Schema for creating a new saved search."""

    name: str = Field(..., min_length=1, max_length=100, description="Search name")
    description: str | None = Field(
        None, description="Optional description of the search"
    )
    search_parameters: dict = Field(
        ..., description="Search criteria and parameters as a dictionary"
    )


class SavedSearchUpdate(BaseModel):
    """Schema for updating an existing saved search."""

    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    search_parameters: dict | None = None


class SavedSearchResponse(BaseModel):
    """Schema for saved search response."""

    id: str
    user_id: str
    name: str
    description: str | None
    search_parameters: dict
    created_at: str
    updated_at: str
    last_used_at: str | None

    class Config:
        from_attributes = True


class SavedSearchExecuteResponse(BaseModel):
    """Schema for execute endpoint response."""

    search_parameters: dict


class SavedSearchDuplicateRequest(BaseModel):
    """Schema for duplicating a saved search."""

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Name for duplicated search (defaults to 'Copy of {original}')",
    )


class SavedSearchStatistics(BaseModel):
    """Schema for search statistics response."""

    total_searches: int
    used_searches: int
    unused_searches: int
    most_recent_search: dict | None


router = APIRouter(prefix="/api/v1/saved-searches", tags=["saved-searches"])


@router.post(
    "", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED
)
def create_saved_search(
    search_data: SavedSearchCreate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Create a new saved search for the current user.

    Saves search criteria including filters, search text, and sorting preferences
    for quick reuse in component searches.
    """
    service = SavedSearchService(db)

    try:
        saved_search = service.create_saved_search(
            user_id=current_user["user_id"],
            name=search_data.name,
            search_parameters=search_data.search_parameters,
            description=search_data.description,
        )

        return {
            "id": saved_search.id,
            "user_id": saved_search.user_id,
            "name": saved_search.name,
            "description": saved_search.description,
            "search_parameters": saved_search.search_parameters,
            "created_at": saved_search.created_at.isoformat(),
            "updated_at": saved_search.updated_at.isoformat(),
            "last_used_at": saved_search.last_used_at.isoformat()
            if saved_search.last_used_at
            else None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create saved search: {str(e)}",
        )


@router.get("", response_model=list[SavedSearchResponse])
def list_saved_searches(
    limit: int = Query(50, ge=1, le=100, description="Number of items to return"),
    offset: int = Query(0, ge=0, description="Number of items to skip"),
    sort_by: str = Query(
        "updated_at",
        pattern="^(created_at|updated_at|last_used_at|name)$",
        description="Sort field",
    ),
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    List all saved searches for the current user.

    Returns searches sorted by the specified field with pagination support.
    """
    service = SavedSearchService(db)

    searches = service.list_user_searches(
        user_id=current_user["user_id"],
        limit=limit,
        offset=offset,
        sort_by=sort_by,
    )

    return [
        {
            "id": search.id,
            "user_id": search.user_id,
            "name": search.name,
            "description": search.description,
            "search_parameters": search.search_parameters,
            "created_at": search.created_at.isoformat(),
            "updated_at": search.updated_at.isoformat(),
            "last_used_at": search.last_used_at.isoformat()
            if search.last_used_at
            else None,
        }
        for search in searches
    ]


@router.get("/stats", response_model=SavedSearchStatistics)
def get_search_statistics(
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Get statistics about the current user's saved searches.

    Returns counts of total, used, and unused searches, plus the most recently used search.
    """
    service = SavedSearchService(db)
    stats = service.get_search_statistics(current_user["user_id"])

    return SavedSearchStatistics(**stats)


@router.get("/{search_id}", response_model=SavedSearchResponse)
def get_saved_search(
    search_id: str,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Get a specific saved search by ID.

    Returns 404 if the search doesn't exist or doesn't belong to the current user.
    """
    try:
        uuid.UUID(search_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid search ID format",
        )

    service = SavedSearchService(db)
    saved_search = service.get_saved_search(search_id, current_user["user_id"])

    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found",
        )

    return {
        "id": saved_search.id,
        "user_id": saved_search.user_id,
        "name": saved_search.name,
        "description": saved_search.description,
        "search_parameters": saved_search.search_parameters,
        "created_at": saved_search.created_at.isoformat(),
        "updated_at": saved_search.updated_at.isoformat(),
        "last_used_at": saved_search.last_used_at.isoformat()
        if saved_search.last_used_at
        else None,
    }


@router.put("/{search_id}", response_model=SavedSearchResponse)
def update_saved_search(
    search_id: str,
    search_update: SavedSearchUpdate,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Update an existing saved search.

    Only the provided fields will be updated. Returns 404 if the search
    doesn't exist or doesn't belong to the current user.
    """
    try:
        uuid.UUID(search_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid search ID format",
        )

    # Filter out None values to only update provided fields
    update_data = {k: v for k, v in search_update.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No data provided for update",
        )

    service = SavedSearchService(db)
    updated_search = service.update_saved_search(
        search_id=search_id,
        user_id=current_user["user_id"],
        name=update_data.get("name"),
        description=update_data.get("description"),
        search_parameters=update_data.get("search_parameters"),
    )

    if not updated_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found",
        )

    return {
        "id": updated_search.id,
        "user_id": updated_search.user_id,
        "name": updated_search.name,
        "description": updated_search.description,
        "search_parameters": updated_search.search_parameters,
        "created_at": updated_search.created_at.isoformat(),
        "updated_at": updated_search.updated_at.isoformat(),
        "last_used_at": updated_search.last_used_at.isoformat()
        if updated_search.last_used_at
        else None,
    }


@router.delete("/{search_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_search(
    search_id: str,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Delete a saved search.

    Returns 404 if the search doesn't exist or doesn't belong to the current user.
    """
    try:
        uuid.UUID(search_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid search ID format",
        )

    service = SavedSearchService(db)
    success = service.delete_saved_search(search_id, current_user["user_id"])

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found",
        )


@router.post("/{search_id}/execute", response_model=SavedSearchExecuteResponse)
def execute_saved_search(
    search_id: str,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Execute a saved search.

    Marks the search as used (updates last_used_at) and returns the search
    parameters to be used with the component search endpoint.

    Returns 404 if the search doesn't exist or doesn't belong to the current user.
    """
    try:
        uuid.UUID(search_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid search ID format",
        )

    service = SavedSearchService(db)

    # Get the search first to return parameters
    saved_search = service.get_saved_search(search_id, current_user["user_id"])
    if not saved_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found",
        )

    # Mark as used
    service.mark_search_as_used(search_id, current_user["user_id"])

    return SavedSearchExecuteResponse(search_parameters=saved_search.search_parameters)


@router.post("/{search_id}/duplicate", response_model=SavedSearchResponse)
def duplicate_saved_search(
    search_id: str,
    duplicate_request: SavedSearchDuplicateRequest | None = None,
    current_user: dict = Depends(require_auth),
    db: Session = Depends(get_db),
):
    """
    Duplicate an existing saved search.

    Creates a copy of the search with a new name. If no name is provided,
    defaults to "Copy of {original_name}".

    Returns 404 if the original search doesn't exist or doesn't belong to the current user.
    """
    try:
        uuid.UUID(search_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid search ID format",
        )

    service = SavedSearchService(db)

    new_name = duplicate_request.name if duplicate_request else None
    duplicated_search = service.duplicate_search(
        search_id=search_id,
        user_id=current_user["user_id"],
        new_name=new_name,
    )

    if not duplicated_search:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Saved search not found",
        )

    return {
        "id": duplicated_search.id,
        "user_id": duplicated_search.user_id,
        "name": duplicated_search.name,
        "description": duplicated_search.description,
        "search_parameters": duplicated_search.search_parameters,
        "created_at": duplicated_search.created_at.isoformat(),
        "updated_at": duplicated_search.updated_at.isoformat(),
        "last_used_at": duplicated_search.last_used_at.isoformat()
        if duplicated_search.last_used_at
        else None,
    }
