"""
External integrations API endpoints.
Provides endpoints for component providers, barcode scanning, KiCad export, and import functionality.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends, Response
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ..services.provider_service import ProviderService
from ..services.import_service import ImportService
from ..services.barcode_service import BarcodeService
from ..services.kicad_service import KiCadExportService
from ..services.kicad_library import KiCadLibraryManager
# from ..auth import require_auth
# Mock auth for MVP - remove in production
def require_auth():
    return None

router = APIRouter(prefix="/api/v1", tags=["integrations"])

# Initialize services
provider_service = ProviderService()
import_service = ImportService()
barcode_service = BarcodeService()
kicad_service = KiCadExportService()
kicad_library = KiCadLibraryManager()


# Request/Response models
class ComponentSearchRequest(BaseModel):
    query: str
    limit: Optional[int] = 20
    providers: Optional[List[str]] = None


class ComponentImportRequest(BaseModel):
    components: List[Dict[str, Any]]
    default_location_id: Optional[str] = None


class BarcodeProcessRequest(BaseModel):
    image_data: str  # Base64 encoded image


class KiCadExportRequest(BaseModel):
    component_ids: Optional[List[str]] = None
    category_id: Optional[str] = None
    manufacturer_name: Optional[str] = None
    library_name: Optional[str] = "PartsHub_Export"


# Provider endpoints
@router.get("/providers/status")
async def get_provider_status():
    """Get status of all component data providers"""
    try:
        status = await import_service.get_provider_status()
        return {"providers": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers/search")
async def search_components_from_providers(
    request: ComponentSearchRequest,
    
):
    """Search for components across external providers"""
    try:
        results = await provider_service.search_components(
            query=request.query,
            limit=request.limit,
            providers=request.providers
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Import endpoints
@router.post("/import/search")
async def import_from_search(
    request: ComponentSearchRequest,
    default_location_id: Optional[str] = None,
    
):
    """Search and import components from external providers"""
    try:
        result = await import_service.import_from_search(
            query=request.query,
            limit=request.limit,
            default_location_id=default_location_id,
            providers=request.providers
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/components")
async def import_components(
    request: ComponentImportRequest,
    
):
    """Import components from prepared data"""
    try:
        result = await import_service.import_components(
            components_data=request.components,
            default_location_id=request.default_location_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Barcode endpoints
@router.post("/barcode/scan")
async def scan_barcode(
    request: BarcodeProcessRequest,
    
):
    """Process barcode scan from image data"""
    try:
        result = await barcode_service.process_barcode_scan(request.image_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/barcode/upload")
async def scan_barcode_file(
    file: UploadFile = File(...),
    
):
    """Scan barcode from uploaded image file"""
    try:
        # Read file content
        content = await file.read()

        # Convert to base64
        import base64
        image_data = base64.b64encode(content).decode('utf-8')

        result = await barcode_service.process_barcode_scan(f"data:image/{file.content_type};base64,{image_data}")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/barcode/info")
async def get_barcode_service_info():
    """Get barcode service information and capabilities"""
    try:
        info = barcode_service.get_service_info()
        return info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# KiCad endpoints
@router.post("/kicad/export")
async def export_kicad_library(
    request: KiCadExportRequest,
    
):
    """Export components to KiCad library format"""
    try:
        if request.component_ids:
            # Export specific components
            from ..models import Component
            from ..database import get_session

            session = get_session()
            try:
                components = session.query(Component).filter(
                    Component.id.in_(request.component_ids)
                ).all()
            finally:
                session.close()

            zip_data = kicad_service.export_component_library(components, request.library_name)

        elif request.category_id:
            zip_data = await kicad_service.export_components_by_category(request.category_id)

        elif request.manufacturer_name:
            zip_data = await kicad_service.export_components_by_manufacturer(request.manufacturer_name)

        else:
            zip_data = await kicad_service.export_all_components()

        return Response(
            content=zip_data,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={request.library_name}.zip"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kicad/component/{component_id}")
async def get_kicad_component_data(
    component_id: str,
    
):
    """Get KiCad library data for a specific component"""
    try:
        data = await kicad_library.get_component_library_data(component_id)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kicad/info")
async def get_kicad_export_info():
    """Get KiCad export service information"""
    try:
        export_info = kicad_service.get_export_info()
        templates_info = kicad_library.get_available_templates()

        return {
            "export": export_info,
            "templates": templates_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# KiCad search endpoint (for tests)
@router.get("/kicad/components")
async def search_kicad_components(
    search: Optional[str] = None,
    library: Optional[str] = None,
    symbol: Optional[str] = None,
    footprint: Optional[str] = None,
    keywords: Optional[str] = None,
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    sort: Optional[str] = "name",
    
):
    """Search components for KiCad export with filtering options"""
    try:
        from ..models import Component, Category
        from ..database import get_session

        session = get_session()
        try:
            query = session.query(Component)

            # Apply filters
            if search:
                query = query.filter(
                    (Component.part_number.ilike(f'%{search}%')) |
                    (Component.description.ilike(f'%{search}%'))
                )

            if keywords:
                query = query.filter(Component.description.ilike(f'%{keywords}%'))

            # Get total count
            total = query.count()

            # Apply pagination
            components = query.offset(offset).limit(limit).all()

            # Format results for KiCad
            results = []
            for component in components:
                results.append({
                    "id": component.id,
                    "part_number": component.part_number,
                    "manufacturer": component.manufacturer if component.manufacturer else None,
                    "category": component.category.name if component.category else None,
                    "description": component.description,
                    "specifications": component.specifications or {},
                    "library": "PartsHub",  # Default library name
                    "symbol": f"{component.part_number}_symbol",
                    "footprint": f"{component.part_number}_footprint"
                })

            return {
                "components": results,
                "total": total,
                "limit": limit,
                "offset": offset
            }

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))