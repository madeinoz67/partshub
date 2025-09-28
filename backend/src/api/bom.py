"""
BOM (Bill of Materials) API endpoints.
Provides endpoints for generating and exporting BOMs with provider integration.
"""

from typing import Any

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from ..services.bom_service import BOMExportFormat, BOMService

router = APIRouter(prefix="/api/v1/bom", tags=["bom"])

# Initialize services
bom_service = BOMService()


# Request/Response models
class ProjectBOMRequest(BaseModel):
    project_id: str
    include_provider_data: bool | None = True
    refresh_provider_data: bool | None = False


class ComponentListBOMRequest(BaseModel):
    components: list[dict[str, Any]]  # [{"component_id": "id", "quantity": 1}]
    include_provider_data: bool | None = True


class BOMExportRequest(BaseModel):
    project_id: str | None = None
    components: list[dict[str, Any]] | None = None
    export_format: str | None = BOMExportFormat.CSV
    include_provider_data: bool | None = True
    refresh_provider_data: bool | None = False


# BOM Generation endpoints
@router.post("/project")
async def generate_project_bom(
    request: ProjectBOMRequest,
):
    """Generate BOM for a specific project"""
    try:
        bom_items = await bom_service.generate_project_bom(
            project_id=request.project_id,
            include_provider_data=request.include_provider_data,
            refresh_provider_data=request.refresh_provider_data,
        )

        # Convert to response format
        items = [item.to_dict() for item in bom_items]
        cost_summary = bom_service.calculate_bom_cost(bom_items)

        return {
            "project_id": request.project_id,
            "items": items,
            "summary": cost_summary,
        }

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/components")
async def generate_component_list_bom(
    request: ComponentListBOMRequest,
):
    """Generate BOM from a list of components and quantities"""
    try:
        # Convert component list to tuples
        component_quantities = [
            (comp["component_id"], comp["quantity"]) for comp in request.components
        ]

        bom_items = await bom_service.generate_component_list_bom(
            component_quantities=component_quantities,
            include_provider_data=request.include_provider_data,
        )

        # Convert to response format
        items = [item.to_dict() for item in bom_items]
        cost_summary = bom_service.calculate_bom_cost(bom_items)

        return {"items": items, "summary": cost_summary}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# BOM Export endpoints
@router.post("/export")
async def export_bom(
    request: BOMExportRequest,
):
    """Export BOM in specified format"""
    try:
        # Generate BOM based on request type
        if request.project_id:
            bom_items = await bom_service.generate_project_bom(
                project_id=request.project_id,
                include_provider_data=request.include_provider_data,
                refresh_provider_data=request.refresh_provider_data,
            )
        elif request.components:
            component_quantities = [
                (comp["component_id"], comp["quantity"]) for comp in request.components
            ]
            bom_items = await bom_service.generate_component_list_bom(
                component_quantities=component_quantities,
                include_provider_data=request.include_provider_data,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either project_id or components must be provided",
            )

        # Export to specified format
        content, mime_type = await bom_service.export_bom(
            bom_items, request.export_format
        )

        # Determine filename
        filename = "bom"
        if request.project_id:
            filename = f"project_{request.project_id}_bom"

        if request.export_format == BOMExportFormat.CSV:
            filename += ".csv"
        elif request.export_format == BOMExportFormat.JSON:
            filename += ".json"
        elif request.export_format == BOMExportFormat.KICAD:
            filename += ".txt"

        return Response(
            content=content,
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}")
async def get_project_bom(
    project_id: str,
    include_provider_data: bool = True,
    refresh_provider_data: bool = False,
):
    """Get BOM for a specific project (GET endpoint)"""
    try:
        bom_items = await bom_service.generate_project_bom(
            project_id=project_id,
            include_provider_data=include_provider_data,
            refresh_provider_data=refresh_provider_data,
        )

        # Convert to response format
        items = [item.to_dict() for item in bom_items]
        cost_summary = bom_service.calculate_bom_cost(bom_items)

        return {"project_id": project_id, "items": items, "summary": cost_summary}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{project_id}/export/{export_format}")
async def export_project_bom(
    project_id: str,
    export_format: str,
    include_provider_data: bool = True,
    refresh_provider_data: bool = False,
):
    """Export project BOM in specified format (GET endpoint)"""
    try:
        # Validate export format
        if export_format not in [
            BOMExportFormat.CSV,
            BOMExportFormat.JSON,
            BOMExportFormat.KICAD,
        ]:
            raise HTTPException(
                status_code=400, detail=f"Unsupported export format: {export_format}"
            )

        bom_items = await bom_service.generate_project_bom(
            project_id=project_id,
            include_provider_data=include_provider_data,
            refresh_provider_data=refresh_provider_data,
        )

        # Export to specified format
        content, mime_type = await bom_service.export_bom(bom_items, export_format)

        # Determine filename
        filename = f"project_{project_id}_bom"
        if export_format == BOMExportFormat.CSV:
            filename += ".csv"
        elif export_format == BOMExportFormat.JSON:
            filename += ".json"
        elif export_format == BOMExportFormat.KICAD:
            filename += ".txt"

        return Response(
            content=content,
            media_type=mime_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/formats")
async def get_export_formats():
    """Get available BOM export formats"""
    return {
        "formats": [
            {
                "value": BOMExportFormat.CSV,
                "label": "CSV (Comma Separated Values)",
                "description": "Standard spreadsheet format",
            },
            {
                "value": BOMExportFormat.JSON,
                "label": "JSON",
                "description": "Structured data format with metadata",
            },
            {
                "value": BOMExportFormat.KICAD,
                "label": "KiCad BOM",
                "description": "KiCad-compatible tab-separated format",
            },
        ]
    }


@router.post("/validate")
async def validate_bom_components(
    request: ComponentListBOMRequest,
):
    """Validate BOM components and check availability"""
    try:
        # Convert component list to tuples
        component_quantities = [
            (comp["component_id"], comp["quantity"]) for comp in request.components
        ]

        bom_items = await bom_service.generate_component_list_bom(
            component_quantities=component_quantities,
            include_provider_data=request.include_provider_data,
        )

        # Validate each item
        validation_results = []
        for item in bom_items:
            data = item.to_dict()
            validation = {
                "component_id": data["component_id"],
                "part_number": data["part_number"],
                "requested_quantity": data["quantity"],
                "available_quantity": data.get("availability"),
                "has_pricing": data.get("unit_cost") is not None,
                "has_provider_data": data.get("provider_sku") is not None,
                "status": "ok",
            }

            # Check availability
            if validation["available_quantity"] is not None:
                if validation["available_quantity"] < validation["requested_quantity"]:
                    validation["status"] = "insufficient_stock"
            else:
                validation["status"] = "unknown_availability"

            validation_results.append(validation)

        # Calculate overall status
        overall_status = "ok"
        if any(v["status"] == "insufficient_stock" for v in validation_results):
            overall_status = "insufficient_stock"
        elif any(v["status"] == "unknown_availability" for v in validation_results):
            overall_status = "partial_availability"

        cost_summary = bom_service.calculate_bom_cost(bom_items)

        return {
            "overall_status": overall_status,
            "items": validation_results,
            "summary": cost_summary,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
