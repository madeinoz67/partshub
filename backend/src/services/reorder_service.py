"""
Reorder alert management service.

Handles alert lifecycle, threshold configuration, and reporting for the
automatic reorder alert system powered by SQLite triggers.
"""

import logging
from datetime import UTC, datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..models import Component, ComponentLocation, ReorderAlert, StorageLocation

logger = logging.getLogger(__name__)


class ReorderService:
    """
    Service for managing reorder alerts and thresholds.

    Alerts are automatically created by database triggers when stock falls
    below configured thresholds. This service provides lifecycle management
    (dismiss, mark as ordered) and reporting capabilities.
    """

    def __init__(self, session: Session):
        """
        Initialize service with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    # ==================== Alert Retrieval ====================

    def get_active_alerts(
        self,
        component_id: Optional[str] = None,
        location_id: Optional[str] = None,
        min_shortage: Optional[int] = None,
    ) -> list[dict]:
        """
        Retrieve active reorder alerts with optional filters.

        Args:
            component_id: Filter by specific component UUID
            location_id: Filter by specific storage location UUID
            min_shortage: Minimum shortage amount to include

        Returns:
            List of active alert dictionaries with component/location details
        """
        # Build query with eager loading to avoid N+1
        query = (
            select(ReorderAlert)
            .options(
                joinedload(ReorderAlert.component_location).joinedload(
                    ComponentLocation.component
                ),
                joinedload(ReorderAlert.component_location).joinedload(
                    ComponentLocation.storage_location
                ),
            )
            .where(ReorderAlert.status == "active")
        )

        # Apply filters
        if component_id:
            query = query.where(ReorderAlert.component_id == component_id)

        if location_id:
            query = query.where(ReorderAlert.storage_location_id == location_id)

        if min_shortage is not None:
            query = query.where(ReorderAlert.shortage_amount >= min_shortage)

        # Order by shortage severity (highest shortage first)
        query = query.order_by(ReorderAlert.shortage_amount.desc())

        alerts = self.session.execute(query).scalars().all()
        return [self._to_dict(alert) for alert in alerts]

    def get_alert_by_id(self, alert_id: int) -> dict:
        """
        Retrieve single alert by ID.

        Args:
            alert_id: Alert primary key

        Returns:
            Alert dictionary with full details

        Raises:
            HTTPException(404): Alert not found
        """
        # Query with eager loading
        stmt = (
            select(ReorderAlert)
            .options(
                joinedload(ReorderAlert.component_location).joinedload(
                    ComponentLocation.component
                ),
                joinedload(ReorderAlert.component_location).joinedload(
                    ComponentLocation.storage_location
                ),
            )
            .where(ReorderAlert.id == alert_id)
        )

        alert = self.session.execute(stmt).scalar_one_or_none()

        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

        return self._to_dict(alert)

    def get_alert_history(
        self, component_id: Optional[str] = None, limit: int = 50
    ) -> list[dict]:
        """
        Retrieve historical alerts (dismissed, ordered, resolved).

        Args:
            component_id: Filter by component UUID
            limit: Max number of records (default 50)

        Returns:
            List of historical alerts, newest first
        """
        query = (
            select(ReorderAlert)
            .options(
                joinedload(ReorderAlert.component_location).joinedload(
                    ComponentLocation.component
                ),
                joinedload(ReorderAlert.component_location).joinedload(
                    ComponentLocation.storage_location
                ),
            )
            .where(
                ReorderAlert.status.in_(["dismissed", "ordered", "resolved"])
            )
            .order_by(ReorderAlert.updated_at.desc())
            .limit(limit)
        )

        if component_id:
            query = query.where(ReorderAlert.component_id == component_id)

        alerts = self.session.execute(query).scalars().all()
        return [self._to_dict(alert) for alert in alerts]

    # ==================== Alert Lifecycle ====================

    def dismiss_alert(self, alert_id: int, notes: Optional[str] = None) -> dict:
        """
        Dismiss an active alert (user acknowledges but won't reorder).

        Args:
            alert_id: Alert to dismiss
            notes: Optional reason for dismissal

        Returns:
            Updated alert dictionary

        Raises:
            HTTPException(404): Alert not found
            HTTPException(400): Alert not active
        """
        alert = self.session.get(ReorderAlert, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

        if alert.status != "active":
            raise HTTPException(
                status_code=400,
                detail=f"Alert {alert_id} is not active (status: {alert.status})",
            )

        # Update alert status
        alert.status = "dismissed"
        alert.dismissed_at = datetime.now(UTC).isoformat()
        alert.updated_at = datetime.now(UTC).isoformat()
        if notes:
            alert.notes = notes

        self.session.flush()

        # Reload with relationships
        self.session.refresh(alert)
        self.session.refresh(alert.component_location, ["component", "storage_location"])

        logger.info(f"Alert {alert_id} dismissed by user")
        return self._to_dict(alert)

    def mark_alert_ordered(self, alert_id: int, notes: Optional[str] = None) -> dict:
        """
        Mark alert as ordered (user placed order with supplier).

        Args:
            alert_id: Alert to update
            notes: Optional order details (PO number, supplier, etc.)

        Returns:
            Updated alert dictionary

        Raises:
            HTTPException(404): Alert not found
            HTTPException(400): Alert not active
        """
        alert = self.session.get(ReorderAlert, alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")

        if alert.status != "active":
            raise HTTPException(
                status_code=400,
                detail=f"Alert {alert_id} is not active (status: {alert.status})",
            )

        # Update alert status
        alert.status = "ordered"
        alert.ordered_at = datetime.now(UTC).isoformat()
        alert.updated_at = datetime.now(UTC).isoformat()
        if notes:
            alert.notes = notes

        self.session.flush()

        # Reload with relationships
        self.session.refresh(alert)
        self.session.refresh(alert.component_location, ["component", "storage_location"])

        logger.info(f"Alert {alert_id} marked as ordered")
        return self._to_dict(alert)

    # ==================== Threshold Management ====================

    def update_reorder_threshold(
        self, component_id: str, location_id: str, threshold: int, enabled: bool = True
    ) -> dict:
        """
        Update reorder threshold for a component at a specific location.

        This will trigger alert checks via SQLite triggers if stock is below threshold.

        Args:
            component_id: Component UUID
            location_id: Storage location UUID
            threshold: New reorder threshold (must be >= 0)
            enabled: Enable/disable reorder monitoring

        Returns:
            Updated ComponentLocation dictionary

        Raises:
            HTTPException(400): Invalid threshold value
            HTTPException(404): ComponentLocation not found
        """
        if threshold < 0:
            raise HTTPException(
                status_code=400, detail="Reorder threshold must be >= 0"
            )

        # Find component_location with pessimistic lock (matches stock_operations pattern)
        stmt = (
            select(ComponentLocation)
            .where(
                ComponentLocation.component_id == component_id,
                ComponentLocation.storage_location_id == location_id,
            )
            .with_for_update(nowait=False)
        )

        comp_loc = self.session.execute(stmt).scalar_one_or_none()
        if not comp_loc:
            raise HTTPException(
                status_code=404,
                detail=f"Component {component_id} not found at location {location_id}",
            )

        # Update threshold and enabled status
        comp_loc.reorder_threshold = threshold
        comp_loc.reorder_enabled = enabled

        self.session.flush()
        self.session.refresh(comp_loc)

        logger.info(
            f"Updated reorder threshold for component {component_id} "
            f"at location {location_id}: threshold={threshold}, enabled={enabled}"
        )

        return {
            "component_location_id": comp_loc.id,
            "component_id": comp_loc.component_id,
            "location_id": comp_loc.storage_location_id,
            "reorder_threshold": comp_loc.reorder_threshold,
            "reorder_enabled": comp_loc.reorder_enabled,
            "current_quantity": comp_loc.quantity_on_hand,
            "needs_reorder": comp_loc.needs_reorder,
        }

    def bulk_update_thresholds(self, updates: list[dict]) -> dict:
        """
        Bulk update reorder thresholds.

        Args:
            updates: List of dicts with keys: component_id, location_id, threshold, enabled

        Returns:
            Dict with success count and errors
        """
        success_count = 0
        errors = []

        for update_data in updates:
            try:
                self.update_reorder_threshold(
                    component_id=update_data["component_id"],
                    location_id=update_data["location_id"],
                    threshold=update_data["threshold"],
                    enabled=update_data.get("enabled", True),
                )
                success_count += 1
            except Exception as e:
                errors.append(
                    {
                        "component_id": update_data.get("component_id"),
                        "location_id": update_data.get("location_id"),
                        "error": str(e),
                    }
                )

        return {"success_count": success_count, "error_count": len(errors), "errors": errors}

    # ==================== Reporting ====================

    def check_low_stock(self) -> list[dict]:
        """
        Query all component_locations where reorder is enabled and stock is below threshold.

        This gives current state. Active alerts are already created by triggers.

        Returns:
            List of dicts with component/location/stock details
        """
        query = (
            select(ComponentLocation)
            .options(
                joinedload(ComponentLocation.component),
                joinedload(ComponentLocation.storage_location),
            )
            .where(
                ComponentLocation.reorder_enabled == True,  # noqa: E712
                ComponentLocation.quantity_on_hand < ComponentLocation.reorder_threshold,
            )
            .order_by(
                (
                    ComponentLocation.reorder_threshold
                    - ComponentLocation.quantity_on_hand
                ).desc()
            )
        )

        low_stock_items = self.session.execute(query).scalars().all()

        return [
            {
                "component_location_id": item.id,
                "component_id": item.component_id,
                "component_name": item.component.name,
                "location_id": item.storage_location_id,
                "location_name": item.storage_location.name,
                "current_quantity": item.quantity_on_hand,
                "reorder_threshold": item.reorder_threshold,
                "shortage_amount": item.reorder_shortage,
            }
            for item in low_stock_items
        ]

    def get_alert_statistics(self) -> dict:
        """
        Get summary statistics for alerts.

        Returns:
            Dict with counts by status, avg shortage, etc.
        """
        stats = {}

        # Count by status
        status_counts = (
            self.session.query(ReorderAlert.status, func.count(ReorderAlert.id))
            .group_by(ReorderAlert.status)
            .all()
        )
        stats["by_status"] = {status: count for status, count in status_counts}

        # Active alert stats
        active_stats = (
            self.session.query(
                func.count(ReorderAlert.id),
                func.avg(ReorderAlert.shortage_amount),
                func.max(ReorderAlert.shortage_amount),
            )
            .filter(ReorderAlert.status == "active")
            .first()
        )

        stats["active_alerts"] = {
            "count": active_stats[0] or 0,
            "avg_shortage": round(float(active_stats[1] or 0), 2),
            "max_shortage": active_stats[2] or 0,
        }

        return stats

    # ==================== Helper Methods ====================

    def _to_dict(self, alert: ReorderAlert) -> dict:
        """
        Convert ORM model to dictionary for response.

        Args:
            alert: ReorderAlert instance with loaded relationships

        Returns:
            Dict with all alert details
        """
        comp_loc = alert.component_location
        component = comp_loc.component
        location = comp_loc.storage_location

        return {
            "id": alert.id,
            "component_location_id": alert.component_location_id,
            "component_id": alert.component_id,
            "component_name": component.name,
            "component_part_number": component.part_number,
            "location_id": alert.storage_location_id,
            "location_name": location.name,
            "status": alert.status,
            "severity": alert.severity,
            "current_quantity": alert.current_quantity,
            "reorder_threshold": alert.reorder_threshold,
            "shortage_amount": alert.shortage_amount,
            "shortage_percentage": round(alert.shortage_percentage, 2),
            "created_at": alert.created_at,
            "updated_at": alert.updated_at,
            "dismissed_at": alert.dismissed_at,
            "ordered_at": alert.ordered_at,
            "resolved_at": alert.resolved_at,
            "notes": alert.notes,
        }
