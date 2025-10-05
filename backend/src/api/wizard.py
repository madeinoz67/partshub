"""
Wizard API endpoints for component creation workflow.

Provides endpoints for fuzzy search autocomplete (manufacturers, footprints)
and wizard-based component creation with provider links and resources.
"""

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth.dependencies import require_admin
from ..database import get_db
from ..services.fuzzy_search_service import FuzzySearchService
from ..services.wizard_service import WizardService

router = APIRouter(prefix="/api/wizard", tags=["wizard"])


# Pydantic schemas
class ManufacturerSuggestion(BaseModel):
    """Manufacturer autocomplete suggestion"""

    id: int | None = None  # None for string-based manufacturers (no table)
    name: str
    score: int | float


class FootprintSuggestion(BaseModel):
    """Footprint autocomplete suggestion"""

    id: int | None = None  # None for string-based footprints (no table)
    name: str
    score: int | float


class ProviderLinkCreate(BaseModel):
    """Provider link data for component creation"""

    provider_id: int
    part_number: str
    part_url: str
    metadata: dict | None = None


class ResourceSelection(BaseModel):
    """Resource selection for download"""

    type: Literal["datasheet", "image", "footprint", "symbol", "model_3d"]
    url: str
    file_name: str


class CreateComponentRequest(BaseModel):
    """Request schema for wizard component creation"""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    part_type: Literal["linked", "local", "meta"]
    manufacturer_id: int | None = None
    manufacturer_name: str | None = None
    footprint_id: int | None = None
    footprint_name: str | None = None
    provider_link: ProviderLinkCreate | None = None
    resource_selections: list[ResourceSelection] | None = None
    specifications: dict | None = None


class ComponentResponse(BaseModel):
    """Component response schema"""

    id: str
    name: str
    description: str | None = None
    part_type: str
    manufacturer: str | None = None
    package: str | None = None
    created_at: str

    class Config:
        from_attributes = True


@router.get("/manufacturers/search", response_model=list[ManufacturerSuggestion])
async def search_manufacturers(
    query: str = Query(..., min_length=1, description="Search query (min 1 character)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results (max 50)"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Search manufacturers using fuzzy matching.

    Returns ranked manufacturer suggestions for autocomplete.
    Uses multi-tier ranking: exact match > prefix match > fuzzy match.

    Args:
        query: Search query string (min 1 character)
        limit: Maximum number of results (default 10, max 50)

    Returns:
        List of ManufacturerSuggestion sorted by score descending

    Requires: Admin authentication
    """
    results = await FuzzySearchService.search_manufacturers(db, query, limit)

    return results


@router.get("/footprints/search", response_model=list[FootprintSuggestion])
async def search_footprints(
    query: str = Query(..., min_length=1, description="Search query (min 1 character)"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results (max 50)"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Search footprints using fuzzy matching.

    Returns ranked footprint suggestions for autocomplete.
    Uses multi-tier ranking: exact match > prefix match > fuzzy match.

    Args:
        query: Search query string (min 1 character)
        limit: Maximum number of results (default 10, max 50)

    Returns:
        List of FootprintSuggestion sorted by score descending

    Requires: Admin authentication
    """
    results = await FuzzySearchService.search_footprints(db, query, limit)

    return results


@router.post("/components", status_code=status.HTTP_201_CREATED)
async def create_component(
    component_data: CreateComponentRequest,
    background_tasks: BackgroundTasks,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Create a component via wizard workflow.

    Handles the complete component creation workflow including:
    - Validation of name, manufacturer, footprint
    - Creation of provider link (for linked parts)
    - Queueing resource downloads (datasheets, images, etc.)
    - Atomic transaction with rollback on failure

    Args:
        component_data: Component creation data including provider link and resources
        background_tasks: FastAPI background tasks for async downloads

    Returns:
        Created Component with relationships loaded

    Raises:
        400: Validation error (name length, char restrictions, duplicate, etc.)
        500: Creation failed (database error)

    Requires: Admin authentication
    """
    try:
        # Convert Pydantic model to dict
        data = component_data.model_dump()

        # Create component via service
        component = await WizardService.create_component(
            db, data, background_tasks=background_tasks
        )

        # Return component response
        # Note: We need to format the response according to ComponentResponse schema
        return {
            "id": component.id,
            "name": component.name,
            "description": component.notes or None,
            "part_type": component_data.part_type,
            "manufacturer": component.manufacturer,
            "package": component.package,
            "created_at": component.created_at.isoformat()
            if component.created_at
            else None,
        }

    except ValueError as e:
        # Validation error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Creation failed
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Component creation failed: {str(e)}",
        )
