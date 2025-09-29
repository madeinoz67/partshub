"""
Reports and analytics API endpoints.
Provides dashboard statistics and comprehensive reporting functionality.

Optimized with proper Pydantic response models and comprehensive error handling.
"""

import json
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth.dependencies import require_auth
from ..database import get_db
from ..services.report_service import ReportService

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


# Response Models for better API documentation and validation
class ComponentStatistics(BaseModel):
    """Component statistics response model."""

    total_components: int = Field(..., description="Total number of components")
    low_stock_components: int = Field(..., description="Number of low stock components")
    out_of_stock_components: int = Field(
        ..., description="Number of out of stock components"
    )
    available_components: int = Field(..., description="Number of available components")


class ProjectStatistics(BaseModel):
    """Project statistics response model."""

    active_projects: int = Field(..., description="Number of active projects")
    total_projects: int = Field(..., description="Total number of projects")


class ActivityStatistics(BaseModel):
    """Activity statistics response model."""

    transactions_last_week: int = Field(
        ..., description="Number of transactions in last week"
    )
    total_inventory_value: float = Field(..., description="Total inventory value")


class DashboardSummaryResponse(BaseModel):
    """Dashboard summary response model."""

    component_statistics: ComponentStatistics
    project_statistics: ProjectStatistics
    activity_statistics: ActivityStatistics
    generated_at: str = Field(
        ..., description="ISO timestamp when report was generated"
    )


class DashboardStatsResponse(BaseModel):
    """Basic dashboard statistics response model."""

    total_components: int = Field(..., description="Total number of components")
    total_categories: int = Field(..., description="Total number of categories")
    total_storage_locations: int = Field(
        ..., description="Total number of storage locations"
    )
    generated_at: str = Field(
        ..., description="ISO timestamp when report was generated"
    )


class CategoryBreakdownItem(BaseModel):
    """Category breakdown item model."""

    category: str = Field(..., description="Category name")
    component_count: int = Field(..., description="Number of components in category")
    total_quantity: int = Field(..., description="Total quantity in category")
    total_value: float = Field(..., description="Total value of category")


class LocationBreakdownItem(BaseModel):
    """Location breakdown item model."""

    location: str = Field(..., description="Location name")
    hierarchy: str = Field(..., description="Location hierarchy path")
    component_count: int = Field(..., description="Number of components in location")
    total_quantity: int = Field(..., description="Total quantity in location")


class TypeBreakdownItem(BaseModel):
    """Component type breakdown item model."""

    component_type: str = Field(..., description="Component type")
    component_count: int = Field(..., description="Number of components of this type")
    total_quantity: int = Field(..., description="Total quantity of this type")


class InventoryBreakdownResponse(BaseModel):
    """Inventory breakdown response model."""

    by_category: list[CategoryBreakdownItem]
    by_location: list[LocationBreakdownItem]
    by_type: list[TypeBreakdownItem]


class ErrorResponse(BaseModel):
    """Standard error response model."""

    detail: str = Field(..., description="Error message")
    error_code: str | None = Field(None, description="Application-specific error code")


@router.get(
    "/dashboard",
    response_model=DashboardSummaryResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get Dashboard Summary",
    description="Retrieve key metrics for the main dashboard including component statistics, project status, and activity metrics.",
)
async def get_dashboard_summary(
    db: Session = Depends(get_db)
) -> DashboardSummaryResponse:
    """Get key metrics for the main dashboard with comprehensive error handling."""
    report_service = ReportService(db)
    return report_service.get_dashboard_summary()


@router.get(
    "/dashboard-stats",
    response_model=DashboardStatsResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get Basic Dashboard Statistics",
    description="Retrieve basic dashboard statistics for first-time setup and overview including entity counts.",
)
async def get_dashboard_stats(db: Session = Depends(get_db)) -> DashboardStatsResponse:
    """Get dashboard statistics for first-time setup and overview with proper validation."""
    report_service = ReportService(db)
    return report_service.get_dashboard_stats()


@router.get(
    "/inventory-breakdown",
    response_model=InventoryBreakdownResponse,
    responses={
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get Inventory Breakdown",
    description="Get detailed inventory breakdown by categories, storage locations, and component types.",
)
async def get_inventory_breakdown(
    db: Session = Depends(get_db)
) -> InventoryBreakdownResponse:
    """Get detailed inventory breakdown by categories and locations with optimized queries."""
    report_service = ReportService(db)
    return report_service.get_inventory_breakdown()


@router.get(
    "/usage-analytics",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid parameters"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get Usage Analytics",
    description="Get component usage analytics over specified period including transaction patterns and daily activity.",
)
async def get_usage_analytics(
    days: int = Query(
        30, ge=1, le=365, description="Number of days to analyze (1-365)", example=30
    ),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get component usage analytics over specified period with parameter validation."""
    report_service = ReportService(db)
    return report_service.get_usage_analytics(days=days)


@router.get("/project-analytics")
async def get_project_analytics(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get project-related analytics and statistics."""
    report_service = ReportService(db)
    return report_service.get_project_analytics()


@router.get("/financial-summary")
async def get_financial_summary(
    months: int = Query(12, ge=1, le=60, description="Number of months to analyze"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get financial analytics for inventory management."""
    report_service = ReportService(db)
    return report_service.get_financial_summary(months=months)


@router.get("/search-analytics")
async def get_search_analytics(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get analytics about search patterns and popular components."""
    report_service = ReportService(db)
    return report_service.get_search_analytics()


@router.get("/system-health")
async def get_system_health_metrics(db: Session = Depends(get_db)) -> dict[str, Any]:
    """Get system health and data quality metrics."""
    report_service = ReportService(db)
    return report_service.get_system_health_metrics()


@router.get("/comprehensive")
async def get_comprehensive_report(
    format: str = Query("json", description="Response format (json, download)"),
    db: Session = Depends(get_db),
):
    """Generate a comprehensive analytical report combining all metrics."""
    report_service = ReportService(db)
    report_data = report_service.generate_comprehensive_report()

    if format == "download":
        # Return as downloadable file
        filename = (
            f"comprehensive-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        )
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return Response(
            content=json.dumps(report_data, indent=2, default=str),
            media_type="application/json",
            headers=headers,
        )
    else:
        # Return as JSON response
        return report_data


@router.get("/export/inventory")
async def export_inventory_report(
    format: str = Query("json", description="Export format (json, csv)"),
    db: Session = Depends(get_db),
):
    """Export detailed inventory report."""
    report_service = ReportService(db)
    report_data = report_service.get_inventory_breakdown()

    filename = f"inventory-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    if format == "csv":
        # Convert to CSV format
        import csv
        import io

        output = io.StringIO()

        # Write category breakdown to CSV
        if report_data.get("by_category"):
            writer = csv.writer(output)
            writer.writerow(
                ["Category", "Component Count", "Total Quantity", "Total Value"]
            )

            for item in report_data["by_category"]:
                writer.writerow(
                    [
                        item["category"],
                        item["component_count"],
                        item["total_quantity"],
                        item["total_value"],
                    ]
                )

        headers = {"Content-Disposition": f'attachment; filename="{filename}.csv"'}
        return Response(
            content=output.getvalue(), media_type="text/csv", headers=headers
        )
    else:
        # JSON format
        headers = {"Content-Disposition": f'attachment; filename="{filename}.json"'}
        return Response(
            content=json.dumps(report_data, indent=2, default=str),
            media_type="application/json",
            headers=headers,
        )


@router.get("/export/usage")
async def export_usage_report(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    format: str = Query("json", description="Export format (json, csv)"),
    db: Session = Depends(get_db),
):
    """Export component usage analytics report."""
    report_service = ReportService(db)
    report_data = report_service.get_usage_analytics(days=days)

    filename = f"usage-report-{days}days-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    if format == "csv":
        # Convert to CSV format
        import csv
        import io

        output = io.StringIO()

        # Write most used components to CSV
        if report_data.get("most_used_components"):
            writer = csv.writer(output)
            writer.writerow(
                [
                    "Component ID",
                    "Part Number",
                    "Name",
                    "Transaction Count",
                    "Total Quantity Moved",
                ]
            )

            for item in report_data["most_used_components"]:
                writer.writerow(
                    [
                        item["component_id"],
                        item["part_number"],
                        item["name"],
                        item["transaction_count"],
                        item["total_quantity_moved"],
                    ]
                )

        headers = {"Content-Disposition": f'attachment; filename="{filename}.csv"'}
        return Response(
            content=output.getvalue(), media_type="text/csv", headers=headers
        )
    else:
        # JSON format
        headers = {"Content-Disposition": f'attachment; filename="{filename}.json"'}
        return Response(
            content=json.dumps(report_data, indent=2, default=str),
            media_type="application/json",
            headers=headers,
        )


@router.get("/export/projects")
async def export_project_report(
    format: str = Query("json", description="Export format (json, csv)"),
    db: Session = Depends(get_db),
):
    """Export project analytics report."""
    report_service = ReportService(db)
    report_data = report_service.get_project_analytics()

    filename = f"project-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    if format == "csv":
        # Convert to CSV format
        import csv
        import io

        output = io.StringIO()

        # Write project status distribution to CSV
        if report_data.get("project_status_distribution"):
            writer = csv.writer(output)
            writer.writerow(["Status", "Count"])

            for item in report_data["project_status_distribution"]:
                writer.writerow([item["status"], item["count"]])

        headers = {"Content-Disposition": f'attachment; filename="{filename}.csv"'}
        return Response(
            content=output.getvalue(), media_type="text/csv", headers=headers
        )
    else:
        # JSON format
        headers = {"Content-Disposition": f'attachment; filename="{filename}.json"'}
        return Response(
            content=json.dumps(report_data, indent=2, default=str),
            media_type="application/json",
            headers=headers,
        )


@router.get("/export/financial")
async def export_financial_report(
    months: int = Query(12, ge=1, le=60, description="Number of months to analyze"),
    format: str = Query("json", description="Export format (json, csv)"),
    db: Session = Depends(get_db),
):
    """Export financial summary report."""
    report_service = ReportService(db)
    report_data = report_service.get_financial_summary(months=months)

    filename = (
        f"financial-report-{months}months-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )

    if format == "csv":
        # Convert to CSV format
        import csv
        import io

        output = io.StringIO()

        # Write top value components to CSV
        if report_data.get("top_value_components"):
            writer = csv.writer(output)
            writer.writerow(["Component ID", "Part Number", "Name", "Inventory Value"])

            for item in report_data["top_value_components"]:
                writer.writerow(
                    [
                        item["component_id"],
                        item["part_number"],
                        item["name"],
                        item["inventory_value"],
                    ]
                )

        headers = {"Content-Disposition": f'attachment; filename="{filename}.csv"'}
        return Response(
            content=output.getvalue(), media_type="text/csv", headers=headers
        )
    else:
        # JSON format
        headers = {"Content-Disposition": f'attachment; filename="{filename}.json"'}
        return Response(
            content=json.dumps(report_data, indent=2, default=str),
            media_type="application/json",
            headers=headers,
        )


@router.get("/export/system-health")
async def export_system_health_report(
    format: str = Query("json", description="Export format (json, csv)"),
    db: Session = Depends(get_db),
):
    """Export system health metrics report."""
    report_service = ReportService(db)
    report_data = report_service.get_system_health_metrics()

    filename = f"system-health-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    if format == "csv":
        # Convert to CSV format
        import csv
        import io

        output = io.StringIO()

        # Write database statistics to CSV
        if report_data.get("database_statistics"):
            writer = csv.writer(output)
            writer.writerow(["Metric", "Value"])

            stats = report_data["database_statistics"]
            for key, value in stats.items():
                writer.writerow([key.replace("_", " ").title(), value])

        headers = {"Content-Disposition": f'attachment; filename="{filename}.csv"'}
        return Response(
            content=output.getvalue(), media_type="text/csv", headers=headers
        )
    else:
        # JSON format
        headers = {"Content-Disposition": f'attachment; filename="{filename}.json"'}
        return Response(
            content=json.dumps(report_data, indent=2, default=str),
            media_type="application/json",
            headers=headers,
        )


# Admin-only detailed reports
@router.get("/admin/data-quality")
async def get_admin_data_quality_report(
    current_user: dict = Depends(require_auth), db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Get detailed data quality report (admin only)."""
    # Note: This would need admin check in production
    report_service = ReportService(db)

    # Combine system health with additional admin-specific metrics
    system_health = report_service.get_system_health_metrics()
    search_analytics = report_service.get_search_analytics()

    return {
        "generated_at": datetime.now().isoformat(),
        "system_health": system_health,
        "search_quality": search_analytics,
        "recommendations": _generate_data_quality_recommendations(
            system_health, search_analytics
        ),
    }


def _generate_data_quality_recommendations(
    system_health: dict[str, Any], search_analytics: dict[str, Any]
) -> list:
    """Generate data quality improvement recommendations."""
    recommendations = []

    # Check data quality metrics
    if system_health.get("data_quality"):
        quality = system_health["data_quality"]

        if quality.get("category_coverage", 0) < 90:
            recommendations.append(
                {
                    "priority": "high",
                    "category": "data_quality",
                    "issue": "Low category coverage",
                    "description": f"Only {quality.get('category_coverage', 0):.1f}% of components have categories assigned",
                    "action": "Review and assign categories to uncategorized components",
                }
            )

        if quality.get("location_coverage", 0) < 85:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "data_quality",
                    "issue": "Low location coverage",
                    "description": f"Only {quality.get('location_coverage', 0):.1f}% of components have storage locations",
                    "action": "Assign storage locations to improve inventory tracking",
                }
            )

        if quality.get("specification_coverage", 0) < 75:
            recommendations.append(
                {
                    "priority": "low",
                    "category": "data_quality",
                    "issue": "Low specification coverage",
                    "description": f"Only {quality.get('specification_coverage', 0):.1f}% of components have detailed specifications",
                    "action": "Add technical specifications to improve component searchability",
                }
            )

    # Check tagging quality
    if search_analytics.get("data_quality"):
        tagging_quality = search_analytics["data_quality"]

        if tagging_quality.get("tagging_percentage", 0) < 60:
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "searchability",
                    "issue": "Low tagging coverage",
                    "description": f"Only {tagging_quality.get('tagging_percentage', 0):.1f}% of components are tagged",
                    "action": "Add relevant tags to improve component discoverability",
                }
            )

    return recommendations
