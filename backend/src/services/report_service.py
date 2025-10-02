"""
ReportService for dashboard statistics and analytics.
Provides comprehensive reporting functionality for inventory insights.

Optimized for performance with proper ComponentLocation joins and comprehensive error handling.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, or_, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..models import (
    Category,
    Component,
    ComponentLocation,
    Project,
    ProjectComponent,
    Purchase,
    StockTransaction,
    StorageLocation,
    Tag,
)

logger = logging.getLogger(__name__)


class ReportService:
    """
    Service for generating dashboard statistics and analytical reports.

    Implements comprehensive error handling, optimized database queries,
    and follows FastAPI best practices for dependency injection.
    """

    def __init__(self, db: Session):
        """Initialize ReportService with database session dependency."""
        self.db = db

    def get_dashboard_summary(self) -> dict[str, Any]:
        """
        Get key metrics for the main dashboard with optimized queries.

        Returns:
            Dict containing component statistics, project statistics, and activity metrics

        Raises:
            HTTPException: 500 if database error occurs
        """
        try:
            # Use a single CTE (Common Table Expression) for efficient stock calculations
            stock_cte = text(
                """
                WITH component_stock_summary AS (
                    SELECT
                        cl.component_id,
                        SUM(cl.quantity_on_hand) as total_quantity,
                        SUM(cl.minimum_stock) as total_minimum_stock,
                        SUM(cl.quantity_on_hand * COALESCE(c.average_purchase_price, 0)) as total_value
                    FROM component_locations cl
                    LEFT JOIN components c ON cl.component_id = c.id
                    GROUP BY cl.component_id
                )
                SELECT
                    COUNT(DISTINCT c.id) as total_components,
                    COUNT(DISTINCT CASE WHEN css.total_quantity <= css.total_minimum_stock
                          AND css.total_minimum_stock > 0 THEN css.component_id END) as low_stock_count,
                    COUNT(DISTINCT CASE WHEN css.total_quantity = 0 THEN css.component_id END) as out_of_stock_count,
                    COALESCE(SUM(css.total_value), 0) as inventory_value
                FROM components c
                LEFT JOIN component_stock_summary css ON c.id = css.component_id
            """
            )

            result = self.db.execute(stock_cte).fetchone()

            if not result:
                raise HTTPException(
                    status_code=500, detail="Failed to calculate component statistics"
                )

            total_components = result.total_components or 0
            low_stock_count = result.low_stock_count or 0
            out_of_stock_count = result.out_of_stock_count or 0
            total_inventory_value = float(result.inventory_value or 0)

            # Active projects count with optimized query
            active_projects = (
                self.db.query(func.count(Project.id))
                .filter(Project.status.in_(["active", "planning"]))
                .scalar()
            ) or 0

            # Total projects count
            total_projects = self.db.query(func.count(Project.id)).scalar() or 0

            # Recent activity with efficient date filtering
            week_ago = datetime.now(UTC) - timedelta(days=7)
            recent_transactions = (
                self.db.query(func.count(StockTransaction.id))
                .filter(StockTransaction.created_at >= week_ago)
                .scalar()
            ) or 0

            return {
                "component_statistics": {
                    "total_components": total_components,
                    "low_stock_components": low_stock_count,
                    "out_of_stock_components": out_of_stock_count,
                    "available_components": total_components - out_of_stock_count,
                },
                "project_statistics": {
                    "active_projects": active_projects,
                    "total_projects": total_projects,
                },
                "activity_statistics": {
                    "transactions_last_week": recent_transactions,
                    "total_inventory_value": total_inventory_value,
                },
                "generated_at": datetime.now(UTC).isoformat(),
            }

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_dashboard_summary: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve dashboard summary due to database error",
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_dashboard_summary: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve dashboard summary"
            )

    def get_dashboard_stats(self) -> dict[str, Any]:
        """
        Get basic dashboard statistics for setup and overview.

        Returns:
            Dict containing basic entity counts

        Raises:
            HTTPException: 500 if database error occurs
        """
        try:
            # Use a single query for efficiency
            stats_query = text(
                """
                SELECT
                    (SELECT COUNT(*) FROM components) as total_components,
                    (SELECT COUNT(*) FROM categories) as total_categories,
                    (SELECT COUNT(*) FROM storage_locations) as total_storage_locations
            """
            )

            result = self.db.execute(stats_query).fetchone()

            if not result:
                raise HTTPException(
                    status_code=500, detail="Failed to retrieve dashboard statistics"
                )

            return {
                "total_components": result.total_components or 0,
                "total_categories": result.total_categories or 0,
                "total_storage_locations": result.total_storage_locations or 0,
                "generated_at": datetime.now(UTC).isoformat(),
            }

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_dashboard_stats: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve dashboard statistics due to database error",
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_dashboard_stats: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve dashboard statistics"
            )

    def get_inventory_breakdown(self) -> dict[str, Any]:
        """
        Get detailed inventory breakdown using optimized single-query approach.

        Returns:
            Dict containing breakdowns by category, location, and component type

        Raises:
            HTTPException: 500 if database error occurs
        """
        try:
            # Single optimized query with CTEs for all breakdowns
            optimized_query = text(
                """
                WITH inventory_aggregates AS (
                    -- Base aggregation with all necessary joins
                    SELECT
                        -- Category information
                        COALESCE(cat.name, 'Uncategorized') as category_name,

                        -- Location information
                        COALESCE(loc.name, 'No Location') as location_name,
                        COALESCE(loc.location_hierarchy, 'Unassigned') as location_hierarchy,

                        -- Component information
                        COALESCE(c.component_type, 'Unknown') as component_type,

                        -- Aggregated metrics
                        cl.component_id,
                        cl.quantity_on_hand,
                        COALESCE(c.average_purchase_price, 0) as unit_price
                    FROM component_locations cl
                    LEFT JOIN components c ON cl.component_id = c.id
                    LEFT JOIN categories cat ON c.category_id = cat.id
                    LEFT JOIN storage_locations loc ON cl.storage_location_id = loc.id
                    WHERE cl.quantity_on_hand >= 0
                ),

                category_breakdown AS (
                    SELECT
                        'category' as breakdown_type,
                        category_name as breakdown_key,
                        NULL as hierarchy,
                        COUNT(DISTINCT component_id) as component_count,
                        SUM(quantity_on_hand) as total_quantity,
                        SUM(quantity_on_hand * unit_price) as total_value
                    FROM inventory_aggregates
                    GROUP BY category_name
                ),

                location_breakdown AS (
                    SELECT
                        'location' as breakdown_type,
                        location_name as breakdown_key,
                        location_hierarchy as hierarchy,
                        COUNT(DISTINCT component_id) as component_count,
                        SUM(quantity_on_hand) as total_quantity,
                        CAST(NULL AS REAL) as total_value
                    FROM inventory_aggregates
                    GROUP BY location_name, location_hierarchy
                ),

                type_breakdown AS (
                    SELECT
                        'type' as breakdown_type,
                        component_type as breakdown_key,
                        NULL as hierarchy,
                        COUNT(DISTINCT component_id) as component_count,
                        SUM(quantity_on_hand) as total_quantity,
                        CAST(NULL AS REAL) as total_value
                    FROM inventory_aggregates
                    WHERE component_type IS NOT NULL
                    GROUP BY component_type
                )

                -- Combine all breakdowns into single result set
                SELECT
                    breakdown_type,
                    breakdown_key,
                    hierarchy,
                    component_count,
                    total_quantity,
                    total_value
                FROM category_breakdown
                UNION ALL
                SELECT
                    breakdown_type,
                    breakdown_key,
                    hierarchy,
                    component_count,
                    total_quantity,
                    total_value
                FROM location_breakdown
                UNION ALL
                SELECT
                    breakdown_type,
                    breakdown_key,
                    hierarchy,
                    component_count,
                    total_quantity,
                    total_value
                FROM type_breakdown
                ORDER BY breakdown_type, component_count DESC
            """
            )

            results = self.db.execute(optimized_query).fetchall()

            # Organize results by breakdown type
            breakdowns = {"by_category": [], "by_location": [], "by_type": []}

            for row in results:
                breakdown_type = row.breakdown_type

                if breakdown_type == "category":
                    breakdowns["by_category"].append(
                        {
                            "category": row.breakdown_key,
                            "component_count": int(row.component_count or 0),
                            "total_quantity": int(row.total_quantity or 0),
                            "total_value": float(row.total_value or 0),
                        }
                    )
                elif breakdown_type == "location":
                    breakdowns["by_location"].append(
                        {
                            "location": row.breakdown_key,
                            "hierarchy": row.hierarchy,
                            "component_count": int(row.component_count or 0),
                            "total_quantity": int(row.total_quantity or 0),
                        }
                    )
                elif breakdown_type == "type":
                    breakdowns["by_type"].append(
                        {
                            "component_type": row.breakdown_key,
                            "component_count": int(row.component_count or 0),
                            "total_quantity": int(row.total_quantity or 0),
                        }
                    )

            return breakdowns

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_inventory_breakdown: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve inventory breakdown due to database error",
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_inventory_breakdown: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve inventory breakdown"
            )

    def get_usage_analytics(self, days: int = 30) -> dict[str, Any]:
        """
        Get component usage analytics over specified period.

        Args:
            days: Number of days to analyze (default 30)

        Returns:
            Dict containing usage analytics and transaction patterns

        Raises:
            HTTPException: 400 if invalid parameters, 500 if database error occurs
        """
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=400, detail="Days parameter must be between 1 and 365"
            )

        try:
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=days)

            # Most used components (by transaction frequency)
            most_used = (
                self.db.query(
                    StockTransaction.component_id,
                    Component.part_number,
                    Component.name,
                    func.count(StockTransaction.id).label("transaction_count"),
                    func.sum(func.abs(StockTransaction.quantity_change)).label(
                        "total_quantity_moved"
                    ),
                )
                .join(Component, StockTransaction.component_id == Component.id)
                .filter(StockTransaction.created_at >= start_date)
                .group_by(
                    StockTransaction.component_id, Component.part_number, Component.name
                )
                .order_by(func.count(StockTransaction.id).desc())
                .limit(10)
                .all()
            )

            # Transaction type distribution
            transaction_types = (
                self.db.query(
                    StockTransaction.transaction_type,
                    func.count(StockTransaction.id).label("count"),
                    func.sum(func.abs(StockTransaction.quantity_change)).label(
                        "total_quantity"
                    ),
                )
                .filter(StockTransaction.created_at >= start_date)
                .group_by(StockTransaction.transaction_type)
                .all()
            )

            # Daily activity trend
            daily_activity = (
                self.db.query(
                    func.date(StockTransaction.created_at).label("date"),
                    func.count(StockTransaction.id).label("transaction_count"),
                )
                .filter(StockTransaction.created_at >= start_date)
                .group_by(func.date(StockTransaction.created_at))
                .order_by(func.date(StockTransaction.created_at))
                .all()
            )

            return {
                "period_days": days,
                "most_used_components": [
                    {
                        "component_id": comp_id,
                        "part_number": part_num or "N/A",
                        "name": name or "Unknown",
                        "transaction_count": int(count),
                        "total_quantity_moved": int(total_qty or 0),
                    }
                    for comp_id, part_num, name, count, total_qty in most_used
                ],
                "transaction_distribution": [
                    {
                        "transaction_type": trans_type.value
                        if hasattr(trans_type, "value")
                        else str(trans_type),
                        "count": int(count),
                        "total_quantity": int(total_qty or 0),
                    }
                    for trans_type, count, total_qty in transaction_types
                ],
                "daily_activity": [
                    {
                        "date": str(date) if date else None,
                        "transaction_count": int(count),
                    }
                    for date, count in daily_activity
                ],
            }

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_usage_analytics: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve usage analytics due to database error",
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_usage_analytics: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve usage analytics"
            )

    def get_project_analytics(self) -> dict[str, Any]:
        """
        Get project-related analytics and statistics.

        Returns:
            Dict containing project status distribution and component allocation data

        Raises:
            HTTPException: 500 if database error occurs
        """
        try:
            # Project status distribution
            project_status = (
                self.db.query(Project.status, func.count(Project.id).label("count"))
                .group_by(Project.status)
                .order_by(func.count(Project.id).desc())
                .all()
            )

            # Most allocated components across all projects
            allocated_components = (
                self.db.query(
                    ProjectComponent.component_id,
                    Component.part_number,
                    Component.name,
                    func.sum(ProjectComponent.quantity_allocated).label(
                        "total_allocated"
                    ),
                    func.count(func.distinct(ProjectComponent.project_id)).label(
                        "project_count"
                    ),
                )
                .join(Component, ProjectComponent.component_id == Component.id)
                .filter(ProjectComponent.quantity_allocated > 0)
                .group_by(
                    ProjectComponent.component_id, Component.part_number, Component.name
                )
                .order_by(func.sum(ProjectComponent.quantity_allocated).desc())
                .limit(10)
                .all()
            )

            # Project value analysis
            project_values = (
                self.db.query(
                    Project.id,
                    Project.name,
                    func.sum(
                        ProjectComponent.quantity_allocated
                        * func.coalesce(Component.average_purchase_price, 0)
                    ).label("estimated_value"),
                )
                .join(ProjectComponent, Project.id == ProjectComponent.project_id)
                .join(Component, ProjectComponent.component_id == Component.id)
                .filter(Component.average_purchase_price.isnot(None))
                .group_by(Project.id, Project.name)
                .order_by(
                    func.sum(
                        ProjectComponent.quantity_allocated
                        * func.coalesce(Component.average_purchase_price, 0)
                    ).desc()
                )
                .limit(10)
                .all()
            )

            return {
                "project_status_distribution": [
                    {"status": status or "Unknown", "count": int(count)}
                    for status, count in project_status
                ],
                "most_allocated_components": [
                    {
                        "component_id": comp_id,
                        "part_number": part_num or "N/A",
                        "name": name or "Unknown",
                        "total_allocated": int(total_alloc),
                        "project_count": int(proj_count),
                    }
                    for comp_id, part_num, name, total_alloc, proj_count in allocated_components
                ],
                "highest_value_projects": [
                    {
                        "project_id": proj_id,
                        "project_name": proj_name or "Unnamed Project",
                        "estimated_value": float(value or 0),
                    }
                    for proj_id, proj_name, value in project_values
                ],
            }

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_project_analytics: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve project analytics due to database error",
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_project_analytics: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve project analytics"
            )

    def get_financial_summary(self, months: int = 12) -> dict[str, Any]:
        """
        Get financial analytics using optimized single-query approach for inventory valuation.

        Args:
            months: Number of months to analyze for purchase trends

        Returns:
            Dict containing financial metrics and top value components

        Raises:
            HTTPException: 500 if database error occurs
        """
        try:
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=months * 30)

            # Single CTE for all financial calculations - major optimization
            financial_cte = text(
                """
                WITH financial_aggregates AS (
                    SELECT
                        c.id as component_id,
                        c.part_number,
                        c.name,
                        c.average_purchase_price,
                        SUM(cl.quantity_on_hand) as total_quantity
                    FROM components c
                    INNER JOIN component_locations cl ON c.id = cl.component_id
                    WHERE c.average_purchase_price IS NOT NULL
                      AND c.average_purchase_price > 0
                      AND cl.quantity_on_hand > 0
                    GROUP BY c.id, c.part_number, c.name, c.average_purchase_price
                ),
                inventory_valuation AS (
                    SELECT
                        SUM(total_quantity * average_purchase_price) as total_value
                    FROM financial_aggregates
                ),
                top_components AS (
                    SELECT
                        component_id,
                        part_number,
                        name,
                        (total_quantity * average_purchase_price) as component_value
                    FROM financial_aggregates
                    ORDER BY component_value DESC
                    LIMIT 10
                )
                SELECT
                    'total_value' as metric_type,
                    NULL as component_id,
                    NULL as part_number,
                    NULL as name,
                    iv.total_value as value
                FROM inventory_valuation iv
                UNION ALL
                SELECT
                    'top_component' as metric_type,
                    tc.component_id,
                    tc.part_number,
                    tc.name,
                    tc.component_value as value
                FROM top_components tc
                ORDER BY metric_type, value DESC
            """
            )

            results = self.db.execute(financial_cte).fetchall()

            # Parse results efficiently
            total_value = 0.0
            top_components = []

            for row in results:
                if row.metric_type == "total_value":
                    total_value = float(row.value or 0)
                elif row.metric_type == "top_component":
                    top_components.append(
                        {
                            "component_id": row.component_id,
                            "part_number": row.part_number or "N/A",
                            "name": row.name or "Unknown",
                            "inventory_value": float(row.value or 0),
                        }
                    )

            # Purchase trends (handled separately for optimal performance)
            monthly_spending = []
            try:
                purchase_trends = (
                    self.db.query(
                        func.date_trunc("month", Purchase.purchase_date).label("month"),
                        func.sum(Purchase.total_cost).label("total_spent"),
                        func.count(Purchase.id).label("purchase_count"),
                    )
                    .filter(Purchase.purchase_date >= start_date)
                    .group_by(func.date_trunc("month", Purchase.purchase_date))
                    .order_by(func.date_trunc("month", Purchase.purchase_date))
                    .all()
                )

                monthly_spending = [
                    {
                        "month": month.isoformat() if month else None,
                        "total_spent": float(total or 0),
                        "purchase_count": int(count),
                    }
                    for month, total, count in purchase_trends
                ]
            except SQLAlchemyError:
                # Purchase table might not exist or have data
                logger.info("Purchase data not available for financial summary")
                monthly_spending = []

            return {
                "current_inventory_value": total_value,
                "monthly_spending": monthly_spending,
                "top_value_components": top_components,
                "analysis_period_months": months,
            }

        except SQLAlchemyError as e:
            logger.error(f"Database error in get_financial_summary: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve financial summary due to database error",
            )
        except Exception as e:
            logger.error(f"Unexpected error in get_financial_summary: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to retrieve financial summary"
            )

    def get_search_analytics(self) -> dict[str, Any]:
        """Get analytics about search patterns and popular components."""
        # Most popular tags (by component count)
        popular_tags = (
            self.db.query(Tag.name, func.count(Component.id).label("component_count"))
            .join(Tag.components)
            .group_by(Tag.id, Tag.name)
            .order_by(func.count(Component.id).desc())
            .limit(10)
            .all()
        )

        # Components with most tags
        well_tagged_components = (
            self.db.query(
                Component.id,
                Component.part_number,
                Component.name,
                func.count(Tag.id).label("tag_count"),
            )
            .join(Component.tags)
            .group_by(Component.id, Component.part_number, Component.name)
            .order_by(func.count(Tag.id).desc())
            .limit(10)
            .all()
        )

        # Components without tags (for data quality)
        untagged_count = (
            self.db.query(Component)
            .outerjoin(Component.tags)
            .group_by(Component.id)
            .having(func.count(Tag.id) == 0)
            .count()
        )

        return {
            "popular_tags": [
                {"tag_name": name, "component_count": int(count)}
                for name, count in popular_tags
            ],
            "well_tagged_components": [
                {
                    "component_id": comp_id,
                    "part_number": part_num,
                    "name": name,
                    "tag_count": int(count),
                }
                for comp_id, part_num, name, count in well_tagged_components
            ],
            "data_quality": {
                "untagged_components": untagged_count,
                "total_components": self.db.query(Component).count(),
                "tagging_percentage": (
                    (self.db.query(Component).count() - untagged_count)
                    / max(1, self.db.query(Component).count())
                    * 100
                ),
            },
        }

    def generate_comprehensive_report(self) -> dict[str, Any]:
        """Generate a comprehensive analytical report combining all metrics."""
        try:
            return {
                "report_metadata": {
                    "generated_at": datetime.now(UTC).isoformat(),
                    "report_type": "comprehensive_analytics",
                },
                "dashboard_summary": self.get_dashboard_summary(),
                "inventory_breakdown": self.get_inventory_breakdown(),
                "usage_analytics": self.get_usage_analytics(days=30),
                "project_analytics": self.get_project_analytics(),
                "financial_summary": self.get_financial_summary(months=6),
                "search_analytics": self.get_search_analytics(),
            }
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {
                "error": "Failed to generate comprehensive report",
                "message": str(e),
                "generated_at": datetime.now(UTC).isoformat(),
            }

    def get_system_health_metrics(self) -> dict[str, Any]:
        """Get system health and data quality metrics."""
        try:
            # Database statistics
            total_components = self.db.query(Component).count()
            total_transactions = self.db.query(StockTransaction).count()
            total_projects = self.db.query(Project).count()

            # Data quality checks
            components_without_category = (
                self.db.query(Component).filter(Component.category_id.is_(None)).count()
            )

            # Components without any location assignment
            components_with_locations = self.db.query(
                func.distinct(ComponentLocation.component_id)
            ).count()
            components_without_location = total_components - components_with_locations

            components_without_specs = (
                self.db.query(Component)
                .filter(
                    or_(
                        Component.specifications.is_(None),
                        Component.specifications == "{}",
                    )
                )
                .count()
            )

            # Performance indicators - average unique components per location
            location_component_counts = (
                self.db.query(func.count(func.distinct(ComponentLocation.component_id)))
                .group_by(ComponentLocation.storage_location_id)
                .all()
            )
            avg_components_per_location = (
                sum(count[0] for count in location_component_counts)
                / len(location_component_counts)
                if location_component_counts
                else 0
            )

            return {
                "database_statistics": {
                    "total_components": total_components,
                    "total_transactions": total_transactions,
                    "total_projects": total_projects,
                    "total_storage_locations": self.db.query(StorageLocation).count(),
                    "total_categories": self.db.query(Category).count(),
                },
                "data_quality": {
                    "components_without_category": components_without_category,
                    "components_without_location": components_without_location,
                    "components_without_specifications": components_without_specs,
                    "category_coverage": (
                        (total_components - components_without_category)
                        / max(1, total_components)
                        * 100
                    ),
                    "location_coverage": (
                        (total_components - components_without_location)
                        / max(1, total_components)
                        * 100
                    ),
                    "specification_coverage": (
                        (total_components - components_without_specs)
                        / max(1, total_components)
                        * 100
                    ),
                },
                "system_metrics": {
                    "avg_components_per_location": float(
                        avg_components_per_location or 0
                    ),
                    "database_health": "good"
                    if all(
                        [
                            total_components > 0,
                            components_without_category < total_components * 0.1,
                            components_without_location < total_components * 0.1,
                        ]
                    )
                    else "needs_attention",
                },
            }

        except Exception as e:
            logger.error(f"Error getting system health metrics: {e}")
            return {"error": "Failed to get system health metrics", "message": str(e)}
