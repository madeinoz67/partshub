"""
Provider API endpoints for wizard feature.

Provides endpoints for listing providers and searching external
component providers (LCSC, Mouser, DigiKey) for parts.
"""


from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth.dependencies import require_admin
from ..database import get_db
from ..services.wizard_provider_service import WizardProviderService

router = APIRouter(prefix="/api/providers", tags=["providers"])


# Pydantic schemas
class ProviderSchema(BaseModel):
    """Provider response schema"""

    id: int
    name: str
    status: str
    api_key_required: bool

    class Config:
        from_attributes = True


class ProviderPartSchema(BaseModel):
    """Schema for a part from a provider search result"""

    part_number: str
    name: str
    description: str | None = None
    manufacturer: str | None = None
    datasheet_url: str | None = None
    image_urls: list[str] = Field(default_factory=list)
    footprint: str | None = None
    provider_url: str | None = None


class ProviderSearchResponse(BaseModel):
    """Response schema for provider search"""

    results: list[ProviderPartSchema]
    total: int


@router.get("/", response_model=list[ProviderSchema])
async def list_providers(
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    List all providers.

    Returns all providers (both active and inactive).
    Client can filter by status if needed.

    Requires: Admin authentication
    """
    # Get all providers (not just active ones)
    from ..models.wizard_provider import Provider

    providers = db.query(Provider).all()

    return providers


@router.get("/{provider_id}/search", response_model=ProviderSearchResponse)
async def search_provider(
    provider_id: int,
    query: str = Query(
        ..., min_length=2, description="Search query (min 2 characters)"
    ),
    limit: int = Query(20, ge=1, le=100, description="Maximum results (max 100)"),
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Search a specific provider for parts.

    Delegates search to the provider's adapter implementation.
    Returns standardized part data from the provider's API.

    Args:
        provider_id: Provider ID to search
        query: Search query string (min 2 characters)
        limit: Maximum number of results (default 20, max 100)

    Returns:
        ProviderSearchResponse with results and total count

    Raises:
        404: Provider not found
        500: Provider API error

    Requires: Admin authentication
    """
    try:
        # Call service to search provider
        search_result = await WizardProviderService.search_provider(
            db, provider_id, query, limit
        )

        return ProviderSearchResponse(
            results=search_result["results"],
            total=len(search_result["results"]),
        )

    except ValueError as e:
        # Provider not found or inactive
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        # Provider API error or other failures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Provider search failed: {str(e)}",
        )


@router.get("/{provider_id}/parts/{part_number}")
async def get_part_details(
    provider_id: int,
    part_number: str,
    _: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get detailed information about a specific part from a provider.

    Fetches complete part details including datasheet URL, specifications, etc.

    Args:
        provider_id: Provider ID
        part_number: Provider's part number

    Returns:
        Part details with datasheet URL and other information

    Raises:
        404: Provider or part not found
        500: Provider API error

    Requires: Admin authentication
    """
    try:
        # Call service to get part details
        part_details = await WizardProviderService.get_part_details(
            db, provider_id, part_number
        )

        return part_details

    except ValueError as e:
        # Provider not found or inactive
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        # Provider API error or other failures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get part details: {str(e)}",
        )
