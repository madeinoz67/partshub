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
from ..services.provider_attachment_service import provider_attachment_service
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


class ProviderSkuSearchRequest(BaseModel):
    provider_sku: str
    providers: Optional[List[str]] = None


class UnifiedSearchRequest(BaseModel):
    query: str
    search_type: Optional[str] = "auto"  # "auto", "part_number", "provider_sku"
    limit: Optional[int] = 50
    providers: Optional[List[str]] = None


class ComponentImportRequest(BaseModel):
    components: List[Dict[str, Any]]
    default_location_id: Optional[str] = None
    download_attachments: Optional[Dict[str, bool]] = None  # {'datasheet': True, 'image': True}


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


@router.post("/providers/search-sku")
async def search_components_by_provider_sku(
    request: ProviderSkuSearchRequest,

):
    """Search for components by provider-specific SKU"""
    try:
        results = await provider_service.search_by_provider_sku(
            provider_sku=request.provider_sku,
            providers=request.providers
        )
        # Filter out None results and format response
        found_results = {k: v for k, v in results.items() if v is not None}
        return {
            "provider_sku": request.provider_sku,
            "results": found_results,
            "total_found": len(found_results),
            "providers_searched": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/providers/unified-search")
async def unified_component_search(
    request: UnifiedSearchRequest,

):
    """Unified search combining part number and provider SKU searches"""
    try:
        results = await provider_service.unified_search(
            query=request.query,
            search_type=request.search_type,
            limit=request.limit,
            providers=request.providers
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Import endpoints
@router.post("/import/search")
async def import_from_search(
    request: ComponentSearchRequest,
    default_location_id: Optional[str] = None,
    download_attachments: Optional[Dict[str, bool]] = None,

):
    """Search and import components from external providers with optional attachment downloads"""
    try:
        result = await import_service.import_from_search(
            query=request.query,
            limit=request.limit,
            default_location_id=default_location_id,
            providers=request.providers
        )

        # Download attachments if requested and components were imported
        if download_attachments and result.get('imported_components'):
            try:
                # Get search results from the import result to match with components
                import_results = result.get('import_details', [])
                components_with_results = []

                for import_detail in import_results:
                    if import_detail.get('status') == 'imported' and import_detail.get('search_result'):
                        component_id = import_detail.get('component_id')
                        search_result = import_detail.get('search_result')
                        if component_id and search_result:
                            # Convert dict back to ComponentSearchResult if needed
                            from ..providers.base_provider import ComponentSearchResult
                            if isinstance(search_result, dict):
                                search_result = ComponentSearchResult(**search_result)
                            components_with_results.append((component_id, search_result))

                if components_with_results:
                    attachment_results = await provider_attachment_service.download_attachments_for_components(
                        components_with_results,
                        download_attachments
                    )
                    result['attachment_downloads'] = attachment_results

            except Exception as e:
                # Don't fail the import if attachment download fails
                result['attachment_download_error'] = str(e)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import/components")
async def import_components(
    request: ComponentImportRequest,

):
    """Import components from prepared data with optional attachment downloads"""
    try:
        result = await import_service.import_components(
            components_data=request.components,
            default_location_id=request.default_location_id
        )

        # Download attachments if requested and components were imported
        if request.download_attachments and result.get('imported_components'):
            try:
                # Match components with their original search results for attachment downloads
                components_with_results = []

                for component_data in request.components:
                    if 'search_result' in component_data:
                        # Find the corresponding imported component
                        for imported in result.get('import_details', []):
                            if (imported.get('status') == 'imported' and
                                imported.get('part_number') == component_data.get('part_number')):

                                component_id = imported.get('component_id')
                                search_result = component_data['search_result']

                                # Convert dict to ComponentSearchResult if needed
                                from ..providers.base_provider import ComponentSearchResult
                                if isinstance(search_result, dict):
                                    search_result = ComponentSearchResult(**search_result)

                                components_with_results.append((component_id, search_result))
                                break

                if components_with_results:
                    attachment_results = await provider_attachment_service.download_attachments_for_components(
                        components_with_results,
                        request.download_attachments
                    )
                    result['attachment_downloads'] = attachment_results

            except Exception as e:
                # Don't fail the import if attachment download fails
                result['attachment_download_error'] = str(e)

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/attachments/download")
async def download_component_attachments(
    component_id: str,
    download_options: Optional[Dict[str, bool]] = None,

):
    """Download attachments for a specific component from its provider data"""
    try:
        # Get component's provider data to find URLs
        from ..models import Component, ComponentProviderData
        from ..database import get_session

        session = get_session()
        try:
            component = session.query(Component).filter(Component.id == component_id).first()
            if not component:
                raise HTTPException(status_code=404, detail="Component not found")

            provider_data = session.query(ComponentProviderData).filter(
                ComponentProviderData.component_id == component_id
            ).first()

            if not provider_data:
                raise HTTPException(status_code=400, detail="No provider data available for this component")

            # Create a ComponentSearchResult from the provider data
            from ..providers.base_provider import ComponentSearchResult
            search_result = ComponentSearchResult(
                provider_id=provider_data.provider_id,
                part_number=component.part_number,
                manufacturer=component.manufacturer,
                description=component.notes,
                specifications=provider_data.specifications or {},
                datasheet_url=provider_data.datasheet_url,
                image_url=provider_data.image_url,
                availability=provider_data.availability or {},
                pricing=provider_data.pricing or {},
                provider_part_id=provider_data.provider_part_id,
                provider_url=provider_data.provider_url
            )

            result = await provider_attachment_service.download_component_attachments(
                component_id, search_result, download_options
            )

            return result

        finally:
            session.close()

    except HTTPException:
        raise
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


# Removed duplicate KiCad components endpoint - now handled by kicad.py