"""
Pydantic schemas for reorder alert management.

This module defines request/response models for reorder alert operations including:
- Alert lifecycle management (dismiss, mark as ordered)
- Threshold configuration (per-location reorder thresholds)
- Alert reporting and statistics

All alert operations are automatically triggered by database triggers when stock
falls below configured thresholds. This API provides visibility and lifecycle management.
"""


from pydantic import BaseModel, Field

# ==================== Request Schemas ====================


class AlertUpdateRequest(BaseModel):
    """
    Request schema for updating alert status (dismiss or mark as ordered).

    Used for both dismiss and mark-ordered operations. Notes field allows
    users to document why an alert was dismissed or provide order details
    (PO number, supplier, expected delivery, etc.).

    Examples:
        Dismiss alert:
            {
                "notes": "Component being phased out - no reorder needed"
            }

        Mark as ordered:
            {
                "notes": "PO-2025-042 placed with Mouser - Expected delivery 2025-11-01"
            }
    """

    notes: str | None = Field(
        None,
        max_length=500,
        description="Optional notes about status change (reason for dismissal, order details, etc.)",
    )


class ThresholdUpdateRequest(BaseModel):
    """
    Request schema for updating reorder threshold at a specific location.

    When enabled, database triggers automatically create alerts when stock
    falls below threshold. Setting threshold=0 with enabled=false disables
    monitoring for that location.

    Examples:
        Enable reorder monitoring:
            {
                "threshold": 50,
                "enabled": true
            }

        Disable reorder monitoring:
            {
                "threshold": 0,
                "enabled": false
            }

        Update threshold only:
            {
                "threshold": 100,
                "enabled": true
            }
    """

    threshold: int = Field(
        ..., ge=0, description="Reorder threshold quantity (must be >= 0)"
    )
    enabled: bool = Field(
        True, description="Enable/disable reorder monitoring for this location"
    )


class BulkThresholdUpdateRequest(BaseModel):
    """
    Request schema for bulk threshold updates across multiple locations.

    Allows batch configuration of reorder thresholds. Failed updates are
    reported individually without affecting successful updates.

    Example:
        {
            "updates": [
                {
                    "component_id": "660e8400-e29b-41d4-a716-446655440001",
                    "location_id": "770e8400-e29b-41d4-a716-446655440001",
                    "threshold": 50,
                    "enabled": true
                },
                {
                    "component_id": "660e8400-e29b-41d4-a716-446655440002",
                    "location_id": "770e8400-e29b-41d4-a716-446655440001",
                    "threshold": 100,
                    "enabled": true
                }
            ]
        }
    """

    updates: list[dict] = Field(
        ...,
        description="List of threshold updates (each dict must have: component_id, location_id, threshold, enabled)",
        min_length=1,
    )


# ==================== Response Schemas ====================


class ReorderAlertResponse(BaseModel):
    """
    Response schema for reorder alert with full details.

    Provides complete alert information including component/location details,
    shortage metrics, workflow timestamps, and calculated severity.

    Severity levels:
    - critical: shortage > 80% of threshold
    - high: shortage > 50% of threshold
    - medium: shortage > 20% of threshold
    - low: shortage <= 20% of threshold
    """

    # Alert identification
    id: int = Field(..., description="Alert primary key ID")
    component_location_id: str = Field(
        ..., description="ComponentLocation ID that triggered this alert"
    )

    # Component information
    component_id: str = Field(..., description="Component UUID")
    component_name: str = Field(..., description="Component name")
    component_part_number: str = Field(..., description="Component part number")

    # Location information
    location_id: str = Field(..., description="Storage location UUID")
    location_name: str = Field(..., description="Storage location name")

    # Alert status and severity
    status: str = Field(
        ...,
        description='Alert status: "active", "dismissed", "ordered", or "resolved"',
    )
    severity: str = Field(
        ..., description='Alert severity: "critical", "high", "medium", or "low"'
    )

    # Stock metrics
    current_quantity: int = Field(
        ..., description="Current stock quantity when alert was last updated"
    )
    reorder_threshold: int = Field(
        ..., description="Reorder threshold that triggered this alert"
    )
    shortage_amount: int = Field(
        ..., description="Shortage amount (threshold - current_quantity)"
    )
    shortage_percentage: float = Field(
        ..., description="Shortage as percentage of threshold (0-100)"
    )

    # Timestamps
    created_at: str = Field(..., description="When alert was first created (ISO 8601)")
    updated_at: str = Field(..., description="When alert was last updated (ISO 8601)")
    dismissed_at: str | None = Field(
        None, description="When alert was dismissed (ISO 8601, null if not dismissed)"
    )
    ordered_at: str | None = Field(
        None,
        description="When alert was marked as ordered (ISO 8601, null if not ordered)",
    )
    resolved_at: str | None = Field(
        None,
        description="When alert was auto-resolved by restocking (ISO 8601, null if not resolved)",
    )

    # User notes
    notes: str | None = Field(
        None, description="User notes (dismissal reason, order details, etc.)"
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True  # Enable ORM mode


class ThresholdUpdateResponse(BaseModel):
    """
    Response schema for successful threshold update.

    Confirms the new threshold configuration and current stock status.
    If stock is currently below threshold and enabled=true, an alert
    will be automatically created by database triggers.
    """

    component_location_id: str = Field(
        ..., description="ComponentLocation ID that was updated"
    )
    component_id: str = Field(..., description="Component UUID")
    location_id: str = Field(..., description="Storage location UUID")
    reorder_threshold: int = Field(..., description="New reorder threshold")
    reorder_enabled: bool = Field(..., description="Reorder monitoring enabled status")
    current_quantity: int = Field(..., description="Current stock quantity at location")
    needs_reorder: bool = Field(
        ...,
        description="True if current stock is below threshold and monitoring is enabled",
    )


class BulkThresholdUpdateResponse(BaseModel):
    """
    Response schema for bulk threshold updates.

    Reports success count and any errors that occurred during batch processing.
    Successful updates are applied even if some updates fail.
    """

    success_count: int = Field(..., description="Number of successful updates")
    error_count: int = Field(..., description="Number of failed updates")
    errors: list[dict] = Field(
        ...,
        description="List of errors (each dict has: component_id, location_id, error)",
    )


class LowStockItem(BaseModel):
    """
    Single low-stock item in report.

    Represents a component location where reorder is enabled and
    stock is below threshold. May or may not have an active alert
    (alerts are created by triggers on stock changes).
    """

    component_location_id: str = Field(..., description="ComponentLocation ID")
    component_id: str = Field(..., description="Component UUID")
    component_name: str = Field(..., description="Component name")
    location_id: str = Field(..., description="Storage location UUID")
    location_name: str = Field(..., description="Storage location name")
    current_quantity: int = Field(..., description="Current stock quantity")
    reorder_threshold: int = Field(..., description="Reorder threshold")
    shortage_amount: int = Field(
        ..., description="Shortage amount (threshold - current_quantity)"
    )


class LowStockReportResponse(BaseModel):
    """
    Response schema for low stock report.

    Real-time report showing all component locations where reorder
    monitoring is enabled and stock is below threshold.
    """

    items: list[LowStockItem] = Field(..., description="List of low stock items")
    total_count: int = Field(..., description="Total number of low stock items")


class AlertStatistics(BaseModel):
    """
    Alert statistics summary response.

    Provides aggregate metrics including counts by status and
    shortage statistics for active alerts.
    """

    by_status: dict[str, int] = Field(
        ..., description='Alert counts by status (e.g., {"active": 5, "resolved": 12})'
    )
    active_alerts: dict = Field(
        ...,
        description='Active alert statistics: {"count": N, "avg_shortage": X.XX, "max_shortage": Y}',
    )


# ==================== List Response Wrappers ====================


class AlertListResponse(BaseModel):
    """
    Response schema for paginated alert lists.

    Used for active alerts and history endpoints.
    """

    alerts: list[ReorderAlertResponse] = Field(..., description="List of alerts")
    total_count: int = Field(..., description="Total number of alerts matching filter")
