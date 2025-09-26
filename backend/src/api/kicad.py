"""
KiCad integration API endpoints.
Provides KiCad-specific endpoints for component search, symbol/footprint data, and library synchronization.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.kicad_service import KiCadExportService
from ..services.kicad_library import KiCadLibraryManager
from ..services.component_service import ComponentService

router = APIRouter(prefix="/api/v1/kicad", tags=["kicad"])

# Initialize services
kicad_service = KiCadExportService()
kicad_library = KiCadLibraryManager()


# Request/Response models
class KiCadComponentResponse(BaseModel):
    """KiCad-formatted component data."""
    model_config = {"protected_namespaces": ()}

    component_id: str
    reference: str
    value: str
    footprint: str
    symbol_library: Optional[str] = None
    symbol_name: Optional[str] = None
    footprint_library: Optional[str] = None
    footprint_name: Optional[str] = None
    model_3d_path: Optional[str] = None
    fields: Dict[str, str] = {}
    specifications: Dict[str, Any] = {}
    manufacturer: Optional[str] = None
    part_number: Optional[str] = None
    datasheet_url: Optional[str] = None


class KiCadSymbolResponse(BaseModel):
    """KiCad symbol data."""
    symbol_library: str
    symbol_name: str
    symbol_reference: str
    pin_count: Optional[int] = None
    symbol_data: Optional[Dict[str, Any]] = None


class KiCadFootprintResponse(BaseModel):
    """KiCad footprint data."""
    footprint_library: str
    footprint_name: str
    footprint_reference: str
    pad_count: Optional[int] = None
    footprint_data: Optional[Dict[str, Any]] = None


class LibrarySyncRequest(BaseModel):
    """Library synchronization request."""
    library_path: str
    categories: Optional[List[str]] = None
    include_symbols: bool = True
    include_footprints: bool = True
    include_3d_models: bool = False


class LibrarySyncResponse(BaseModel):
    """Library synchronization response."""
    success: bool
    components_exported: int
    symbols_created: int
    footprints_created: int
    models_created: int
    library_path: str
    message: str


# T064: GET /api/v1/kicad/components - Search components for KiCad
@router.get("/components", response_model=List[KiCadComponentResponse])
def search_kicad_components(
    search: Optional[str] = Query(None, description="Search query for component name, part number, or value"),
    package: Optional[str] = Query(None, description="Filter by package type (0805, DIP8, etc.)"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    manufacturer: Optional[str] = Query(None, description="Filter by manufacturer"),
    limit: int = Query(50, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Result offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Search components formatted for KiCad integration.

    Returns components with KiCad-specific formatting including symbol and footprint
    references suitable for direct use in KiCad schematic and PCB design.
    """
    component_service = ComponentService(db)

    # Build search filters
    filters = {}
    if package:
        filters['package'] = package
    if category_id:
        filters['category_id'] = category_id
    if manufacturer:
        filters['manufacturer'] = manufacturer

    # Search components
    components = component_service.search_components(
        query=search,
        filters=filters,
        limit=limit,
        offset=offset
    )

    # Format for KiCad
    kicad_components = []
    for component in components:
        kicad_data = kicad_service.format_component_for_kicad(component)
        kicad_components.append(KiCadComponentResponse(**kicad_data))

    return kicad_components


# T065: GET /api/v1/kicad/components/{id} - Get component details for KiCad
@router.get("/components/{component_id}", response_model=KiCadComponentResponse)
def get_kicad_component(
    component_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed component information formatted for KiCad.

    Returns comprehensive component data including all KiCad-specific fields,
    symbol/footprint references, and specifications in KiCad-compatible format.
    """
    component_service = ComponentService(db)
    component = component_service.get_component(component_id)

    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    # Format for KiCad with full details
    kicad_data = kicad_service.format_component_for_kicad(component, include_full_specs=True)
    return KiCadComponentResponse(**kicad_data)


# T066: GET /api/v1/kicad/components/{id}/symbol - Get symbol data
@router.get("/components/{component_id}/symbol", response_model=KiCadSymbolResponse)
def get_kicad_symbol(
    component_id: str,
    db: Session = Depends(get_db)
):
    """
    Get KiCad symbol data for a component.

    Returns symbol library reference and metadata for use in KiCad schematic editor.
    """
    component_service = ComponentService(db)
    component = component_service.get_component(component_id)

    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    if not component.kicad_data or not component.kicad_data.has_symbol:
        raise HTTPException(status_code=404, detail="No KiCad symbol data available for this component")

    symbol_data = kicad_service.get_symbol_data(component)
    return KiCadSymbolResponse(**symbol_data)


# T067: GET /api/v1/kicad/components/{id}/footprint - Get footprint data
@router.get("/components/{component_id}/footprint", response_model=KiCadFootprintResponse)
def get_kicad_footprint(
    component_id: str,
    db: Session = Depends(get_db)
):
    """
    Get KiCad footprint data for a component.

    Returns footprint library reference and metadata for use in KiCad PCB editor.
    """
    component_service = ComponentService(db)
    component = component_service.get_component(component_id)

    if not component:
        raise HTTPException(status_code=404, detail="Component not found")

    if not component.kicad_data or not component.kicad_data.has_footprint:
        raise HTTPException(status_code=404, detail="No KiCad footprint data available for this component")

    footprint_data = kicad_service.get_footprint_data(component)
    return KiCadFootprintResponse(**footprint_data)


# T068: POST /api/v1/kicad/libraries/sync - Library synchronization
@router.post("/libraries/sync", response_model=LibrarySyncResponse)
def sync_kicad_libraries(
    request: LibrarySyncRequest,
    db: Session = Depends(get_db)
):
    """
    Synchronize PartsHub components to KiCad libraries.

    Exports component data to KiCad-compatible library files including symbols,
    footprints, and 3D models based on configuration.
    """
    try:
        # Validate library path
        import os
        if not os.path.exists(os.path.dirname(request.library_path)):
            raise HTTPException(status_code=400, detail="Library path directory does not exist")

        # Perform synchronization
        sync_result = kicad_library.sync_libraries(
            library_path=request.library_path,
            category_filters=request.categories,
            include_symbols=request.include_symbols,
            include_footprints=request.include_footprints,
            include_3d_models=request.include_3d_models
        )

        return LibrarySyncResponse(
            success=True,
            components_exported=sync_result.get('components_exported', 0),
            symbols_created=sync_result.get('symbols_created', 0),
            footprints_created=sync_result.get('footprints_created', 0),
            models_created=sync_result.get('models_created', 0),
            library_path=request.library_path,
            message=f"Successfully synchronized {sync_result.get('components_exported', 0)} components to KiCad libraries"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Library synchronization failed: {str(e)}")


# Additional utility endpoints

@router.get("/libraries/status")
def get_library_status(db: Session = Depends(get_db)):
    """Get status of KiCad library integration."""
    component_service = ComponentService(db)

    total_components = component_service.count_components()
    components_with_kicad = component_service.count_components_with_kicad_data()

    return {
        "total_components": total_components,
        "components_with_kicad_data": components_with_kicad,
        "coverage_percentage": (components_with_kicad / total_components * 100) if total_components > 0 else 0,
        "library_manager_available": True
    }


@router.get("/field-mappings")
def get_kicad_field_mappings():
    """Get standard KiCad field mappings used by PartsHub."""
    return kicad_service.get_standard_field_mappings()