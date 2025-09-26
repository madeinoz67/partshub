"""
ReportService for dashboard statistics and analytics.
Provides comprehensive reporting functionality for inventory insights.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, func, desc, text
from datetime import datetime, timedelta
from ..models import (
    Component, StockTransaction, TransactionType, Project, ProjectComponent,
    Category, StorageLocation, Tag, Purchase, PurchaseItem
)
import logging

logger = logging.getLogger(__name__)


class ReportService:
    """Service for generating dashboard statistics and analytical reports."""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get key metrics for the main dashboard."""
        # Component counts
        total_components = self.db.query(Component).count()

        # Stock status counts
        low_stock_count = (
            self.db.query(Component)
            .filter(Component.quantity_on_hand <= Component.minimum_stock)
            .filter(Component.minimum_stock > 0)
            .count()
        )

        out_of_stock_count = (
            self.db.query(Component)
            .filter(Component.quantity_on_hand == 0)
            .count()
        )

        # Active projects
        active_projects = (
            self.db.query(Project)
            .filter(Project.status.in_(["active", "planning"]))
            .count()
        )

        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_transactions = (
            self.db.query(StockTransaction)
            .filter(StockTransaction.created_at >= week_ago)
            .count()
        )

        # Inventory valuation
        total_value_result = (
            self.db.query(
                func.sum(Component.quantity_on_hand * Component.average_purchase_price)
            )
            .filter(Component.average_purchase_price.isnot(None))
            .scalar()
        )
        total_inventory_value = float(total_value_result) if total_value_result else 0.0

        return {
            "component_statistics": {
                "total_components": total_components,
                "low_stock_components": low_stock_count,
                "out_of_stock_components": out_of_stock_count,
                "available_components": total_components - out_of_stock_count
            },
            "project_statistics": {
                "active_projects": active_projects,
                "total_projects": self.db.query(Project).count()
            },
            "activity_statistics": {
                "transactions_last_week": recent_transactions,
                "total_inventory_value": total_inventory_value
            },
            "generated_at": datetime.utcnow().isoformat()
        }

    def get_inventory_breakdown(self) -> Dict[str, Any]:
        """Get detailed inventory breakdown by categories and locations."""
        # By category
        category_breakdown = (
            self.db.query(
                Category.name,
                func.count(Component.id).label('component_count'),
                func.sum(Component.quantity_on_hand).label('total_quantity'),
                func.sum(Component.quantity_on_hand * Component.average_purchase_price).label('total_value')
            )
            .outerjoin(Component)
            .group_by(Category.id, Category.name)
            .all()
        )

        # By storage location
        location_breakdown = (
            self.db.query(
                StorageLocation.name,
                StorageLocation.location_hierarchy,
                func.count(Component.id).label('component_count'),
                func.sum(Component.quantity_on_hand).label('total_quantity')
            )
            .outerjoin(Component)
            .group_by(StorageLocation.id, StorageLocation.name, StorageLocation.location_hierarchy)
            .all()
        )

        # By component type
        type_breakdown = (
            self.db.query(
                Component.component_type,
                func.count(Component.id).label('component_count'),
                func.sum(Component.quantity_on_hand).label('total_quantity')
            )
            .filter(Component.component_type.isnot(None))
            .group_by(Component.component_type)
            .order_by(func.count(Component.id).desc())
            .all()
        )

        return {
            "by_category": [
                {
                    "category": name,
                    "component_count": int(count or 0),
                    "total_quantity": int(total_qty or 0),
                    "total_value": float(total_val or 0)
                }
                for name, count, total_qty, total_val in category_breakdown
            ],
            "by_location": [
                {
                    "location": name,
                    "hierarchy": hierarchy,
                    "component_count": int(count or 0),
                    "total_quantity": int(total_qty or 0)
                }
                for name, hierarchy, count, total_qty in location_breakdown
            ],
            "by_type": [
                {
                    "component_type": comp_type,
                    "component_count": int(count or 0),
                    "total_quantity": int(total_qty or 0)
                }
                for comp_type, count, total_qty in type_breakdown
            ]
        }

    def get_usage_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get component usage analytics over specified period."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Most used components (by transaction frequency)
        most_used = (
            self.db.query(
                StockTransaction.component_id,
                Component.part_number,
                Component.name,
                func.count(StockTransaction.id).label('transaction_count'),
                func.sum(func.abs(StockTransaction.quantity_change)).label('total_quantity_moved')
            )
            .join(Component)
            .filter(StockTransaction.created_at >= start_date)
            .group_by(StockTransaction.component_id, Component.part_number, Component.name)
            .order_by(func.count(StockTransaction.id).desc())
            .limit(10)
            .all()
        )

        # Transaction type distribution
        transaction_types = (
            self.db.query(
                StockTransaction.transaction_type,
                func.count(StockTransaction.id).label('count'),
                func.sum(func.abs(StockTransaction.quantity_change)).label('total_quantity')
            )
            .filter(StockTransaction.created_at >= start_date)
            .group_by(StockTransaction.transaction_type)
            .all()
        )

        # Daily activity trend
        daily_activity = (
            self.db.query(
                func.date(StockTransaction.created_at).label('date'),
                func.count(StockTransaction.id).label('transaction_count')
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
                    "part_number": part_num,
                    "name": name,
                    "transaction_count": int(count),
                    "total_quantity_moved": int(total_qty or 0)
                }
                for comp_id, part_num, name, count, total_qty in most_used
            ],
            "transaction_distribution": [
                {
                    "transaction_type": trans_type.value if hasattr(trans_type, 'value') else str(trans_type),
                    "count": int(count),
                    "total_quantity": int(total_qty or 0)
                }
                for trans_type, count, total_qty in transaction_types
            ],
            "daily_activity": [
                {
                    "date": date.isoformat() if date else None,
                    "transaction_count": int(count)
                }
                for date, count in daily_activity
            ]
        }

    def get_project_analytics(self) -> Dict[str, Any]:
        """Get project-related analytics and statistics."""
        # Project status distribution
        project_status = (
            self.db.query(
                Project.status,
                func.count(Project.id).label('count')
            )
            .group_by(Project.status)
            .all()
        )

        # Most allocated components across all projects
        allocated_components = (
            self.db.query(
                ProjectComponent.component_id,
                Component.part_number,
                Component.name,
                func.sum(ProjectComponent.quantity_allocated).label('total_allocated'),
                func.count(ProjectComponent.project_id).label('project_count')
            )
            .join(Component)
            .filter(ProjectComponent.quantity_allocated > 0)
            .group_by(ProjectComponent.component_id, Component.part_number, Component.name)
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
                    ProjectComponent.quantity_allocated * Component.average_purchase_price
                ).label('estimated_value')
            )
            .join(ProjectComponent)
            .join(Component)
            .filter(Component.average_purchase_price.isnot(None))
            .group_by(Project.id, Project.name)
            .order_by(func.sum(
                ProjectComponent.quantity_allocated * Component.average_purchase_price
            ).desc())
            .limit(10)
            .all()
        )

        return {
            "project_status_distribution": [
                {
                    "status": status,
                    "count": int(count)
                }
                for status, count in project_status
            ],
            "most_allocated_components": [
                {
                    "component_id": comp_id,
                    "part_number": part_num,
                    "name": name,
                    "total_allocated": int(total_alloc),
                    "project_count": int(proj_count)
                }
                for comp_id, part_num, name, total_alloc, proj_count in allocated_components
            ],
            "highest_value_projects": [
                {
                    "project_id": proj_id,
                    "project_name": proj_name,
                    "estimated_value": float(value or 0)
                }
                for proj_id, proj_name, value in project_values
            ]
        }

    def get_financial_summary(self, months: int = 12) -> Dict[str, Any]:
        """Get financial analytics for inventory management."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months * 30)

        # Current inventory valuation
        current_valuation = (
            self.db.query(
                func.sum(Component.quantity_on_hand * Component.average_purchase_price)
            )
            .filter(Component.average_purchase_price.isnot(None))
            .scalar()
        )
        current_value = float(current_valuation) if current_valuation else 0.0

        # Purchase trends (if purchase data exists)
        try:
            purchase_trends = (
                self.db.query(
                    func.date_trunc('month', Purchase.purchase_date).label('month'),
                    func.sum(Purchase.total_amount).label('total_spent'),
                    func.count(Purchase.id).label('purchase_count')
                )
                .filter(Purchase.purchase_date >= start_date)
                .group_by(func.date_trunc('month', Purchase.purchase_date))
                .order_by(func.date_trunc('month', Purchase.purchase_date))
                .all()
            )

            monthly_spending = [
                {
                    "month": month.isoformat() if month else None,
                    "total_spent": float(total or 0),
                    "purchase_count": int(count)
                }
                for month, total, count in purchase_trends
            ]
        except Exception:
            # Purchase table might not exist or have data
            monthly_spending = []

        # Top value components
        top_value_components = (
            self.db.query(
                Component.id,
                Component.part_number,
                Component.name,
                (Component.quantity_on_hand * Component.average_purchase_price).label('total_value')
            )
            .filter(Component.average_purchase_price.isnot(None))
            .filter(Component.quantity_on_hand > 0)
            .order_by((Component.quantity_on_hand * Component.average_purchase_price).desc())
            .limit(10)
            .all()
        )

        return {
            "current_inventory_value": current_value,
            "monthly_spending": monthly_spending,
            "top_value_components": [
                {
                    "component_id": comp_id,
                    "part_number": part_num,
                    "name": name,
                    "inventory_value": float(value or 0)
                }
                for comp_id, part_num, name, value in top_value_components
            ],
            "analysis_period_months": months
        }

    def get_search_analytics(self) -> Dict[str, Any]:
        """Get analytics about search patterns and popular components."""
        # Most popular tags (by component count)
        popular_tags = (
            self.db.query(
                Tag.name,
                func.count(Component.id).label('component_count')
            )
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
                func.count(Tag.id).label('tag_count')
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
                {
                    "tag_name": name,
                    "component_count": int(count)
                }
                for name, count in popular_tags
            ],
            "well_tagged_components": [
                {
                    "component_id": comp_id,
                    "part_number": part_num,
                    "name": name,
                    "tag_count": int(count)
                }
                for comp_id, part_num, name, count in well_tagged_components
            ],
            "data_quality": {
                "untagged_components": untagged_count,
                "total_components": self.db.query(Component).count(),
                "tagging_percentage": (
                    (self.db.query(Component).count() - untagged_count) /
                    max(1, self.db.query(Component).count()) * 100
                )
            }
        }

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analytical report combining all metrics."""
        try:
            return {
                "report_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "report_type": "comprehensive_analytics"
                },
                "dashboard_summary": self.get_dashboard_summary(),
                "inventory_breakdown": self.get_inventory_breakdown(),
                "usage_analytics": self.get_usage_analytics(days=30),
                "project_analytics": self.get_project_analytics(),
                "financial_summary": self.get_financial_summary(months=6),
                "search_analytics": self.get_search_analytics()
            }
        except Exception as e:
            logger.error(f"Error generating comprehensive report: {e}")
            return {
                "error": "Failed to generate comprehensive report",
                "message": str(e),
                "generated_at": datetime.utcnow().isoformat()
            }

    def get_system_health_metrics(self) -> Dict[str, Any]:
        """Get system health and data quality metrics."""
        try:
            # Database statistics
            total_components = self.db.query(Component).count()
            total_transactions = self.db.query(StockTransaction).count()
            total_projects = self.db.query(Project).count()

            # Data quality checks
            components_without_category = (
                self.db.query(Component)
                .filter(Component.category_id.is_(None))
                .count()
            )

            components_without_location = (
                self.db.query(Component)
                .filter(Component.storage_location_id.is_(None))
                .count()
            )

            components_without_specs = (
                self.db.query(Component)
                .filter(or_(
                    Component.specifications.is_(None),
                    Component.specifications == '{}'
                ))
                .count()
            )

            # Performance indicators
            avg_components_per_location = (
                self.db.query(func.avg(
                    self.db.query(func.count(Component.id))
                    .filter(Component.storage_location_id == StorageLocation.id)
                    .scalar_subquery()
                ))
                .scalar()
            )

            return {
                "database_statistics": {
                    "total_components": total_components,
                    "total_transactions": total_transactions,
                    "total_projects": total_projects,
                    "total_storage_locations": self.db.query(StorageLocation).count(),
                    "total_categories": self.db.query(Category).count()
                },
                "data_quality": {
                    "components_without_category": components_without_category,
                    "components_without_location": components_without_location,
                    "components_without_specifications": components_without_specs,
                    "category_coverage": (
                        (total_components - components_without_category) / max(1, total_components) * 100
                    ),
                    "location_coverage": (
                        (total_components - components_without_location) / max(1, total_components) * 100
                    ),
                    "specification_coverage": (
                        (total_components - components_without_specs) / max(1, total_components) * 100
                    )
                },
                "system_metrics": {
                    "avg_components_per_location": float(avg_components_per_location or 0),
                    "database_health": "good" if all([
                        total_components > 0,
                        components_without_category < total_components * 0.1,
                        components_without_location < total_components * 0.1
                    ]) else "needs_attention"
                }
            }

        except Exception as e:
            logger.error(f"Error getting system health metrics: {e}")
            return {
                "error": "Failed to get system health metrics",
                "message": str(e)
            }