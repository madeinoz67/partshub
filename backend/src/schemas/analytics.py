"""
Pydantic schemas for stock analytics API contracts.

This module defines request/response models for stock analytics and forecasting:
- Time-series stock level data for chart visualization
- Usage trend analysis with velocity metrics
- Moving average forecasting with reorder suggestions
- Dashboard summary metrics

All analytics are derived from stock_transactions and component_locations tables.
Designed for Chart.js integration in Vue.js frontend.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

# ==================== Enums ====================


class AggregationPeriod(str, Enum):
    """Time aggregation period for analytics queries."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ForecastHorizon(str, Enum):
    """Forecast time horizon options."""

    WEEK = "7d"  # 7 days
    TWO_WEEKS = "14d"  # 14 days
    MONTH = "30d"  # 30 days
    QUARTER = "90d"  # 90 days


# ==================== Base Schemas ====================


class DateRangeFilter(BaseModel):
    """
    Date range filter for time-series queries.

    Used across all analytics endpoints to constrain data to specific time windows.
    Defaults to last 30 days if not specified.

    Examples:
        Last 30 days (default):
            {
                "start_date": "2025-09-16T00:00:00Z",
                "end_date": "2025-10-16T00:00:00Z"
            }

        Custom range:
            {
                "start_date": "2025-01-01T00:00:00Z",
                "end_date": "2025-03-31T23:59:59Z"
            }
    """

    start_date: datetime = Field(
        ..., description="Start of date range (ISO 8601 timestamp, inclusive)"
    )
    end_date: datetime = Field(
        ..., description="End of date range (ISO 8601 timestamp, inclusive)"
    )


# ==================== Stock Time-Series Schemas ====================


class StockDataPoint(BaseModel):
    """
    Single data point in stock level time-series.

    Represents aggregated stock quantity at a specific point in time.
    Aggregation level depends on requested period (daily/weekly/monthly).
    """

    timestamp: datetime = Field(
        ..., description="Timestamp for this data point (ISO 8601)"
    )
    quantity: int = Field(..., description="Stock quantity at this timestamp", ge=0)
    transaction_count: int = Field(
        0,
        description="Number of transactions that occurred in this period",
        ge=0,
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "timestamp": "2025-10-16T00:00:00Z",
                "quantity": 150,
                "transaction_count": 5,
            }
        }


class StockLevelsRequest(BaseModel):
    """
    Request schema for stock level time-series data.

    Query parameters for fetching historical stock levels over time.
    Used to generate line charts showing stock trends.

    Examples:
        Daily stock levels for last 30 days:
            {
                "component_id": "660e8400-e29b-41d4-a716-446655440001",
                "location_id": "770e8400-e29b-41d4-a716-446655440001",
                "start_date": "2025-09-16T00:00:00Z",
                "end_date": "2025-10-16T00:00:00Z",
                "period": "daily"
            }

        Monthly aggregation for one year:
            {
                "component_id": "660e8400-e29b-41d4-a716-446655440001",
                "location_id": null,
                "start_date": "2024-10-16T00:00:00Z",
                "end_date": "2025-10-16T00:00:00Z",
                "period": "monthly"
            }
    """

    component_id: str = Field(..., description="Component UUID to analyze")
    location_id: str | None = Field(
        None,
        description="Optional storage location UUID (null = aggregate all locations)",
    )
    start_date: datetime = Field(..., description="Start of date range (ISO 8601)")
    end_date: datetime = Field(..., description="End of date range (ISO 8601)")
    period: AggregationPeriod = Field(
        AggregationPeriod.DAILY,
        description="Time aggregation period (daily, weekly, monthly)",
    )


class StockLevelsResponse(BaseModel):
    """
    Response schema for stock level time-series data.

    Returns historical stock levels aggregated by requested time period.
    Designed for Chart.js line chart visualization.

    Metadata provides context for chart configuration (labels, tooltips, etc.).
    """

    component_id: str = Field(..., description="Component UUID")
    component_name: str = Field(..., description="Component name")
    location_id: str | None = Field(
        None, description="Storage location UUID (null = all locations)"
    )
    location_name: str | None = Field(
        None, description="Storage location name (null = all locations)"
    )
    period: AggregationPeriod = Field(..., description="Time aggregation period used")
    data: list[StockDataPoint] = Field(
        ..., description="Time-series stock level data points"
    )
    metadata: dict = Field(
        ...,
        description="Additional metadata (date range, current stock, reorder threshold)",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "component_id": "660e8400-e29b-41d4-a716-446655440001",
                "component_name": "Ceramic Capacitor 100nF 0805",
                "location_id": "770e8400-e29b-41d4-a716-446655440001",
                "location_name": "Bin A-12",
                "period": "daily",
                "data": [
                    {
                        "timestamp": "2025-10-01T00:00:00Z",
                        "quantity": 200,
                        "transaction_count": 2,
                    },
                    {
                        "timestamp": "2025-10-02T00:00:00Z",
                        "quantity": 180,
                        "transaction_count": 1,
                    },
                ],
                "metadata": {
                    "start_date": "2025-10-01T00:00:00Z",
                    "end_date": "2025-10-16T00:00:00Z",
                    "current_quantity": 150,
                    "reorder_threshold": 100,
                },
            }
        }


# ==================== Usage Trends Schemas ====================


class VelocityMetrics(BaseModel):
    """
    Consumption velocity metrics for a component.

    Measures how quickly stock is being consumed over different time windows.
    Used to identify usage patterns and predict future consumption.
    """

    daily_average: float = Field(
        ...,
        description="Average daily consumption (units/day)",
        ge=0,
    )
    weekly_average: float = Field(
        ...,
        description="Average weekly consumption (units/week)",
        ge=0,
    )
    monthly_average: float = Field(
        ...,
        description="Average monthly consumption (units/month)",
        ge=0,
    )
    total_consumed: int = Field(
        ..., description="Total units consumed in analysis period", ge=0
    )
    days_analyzed: int = Field(
        ..., description="Number of days in analysis period", ge=1
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "daily_average": 3.5,
                "weekly_average": 24.5,
                "monthly_average": 105.0,
                "total_consumed": 315,
                "days_analyzed": 90,
            }
        }


class UsageTrendDataPoint(BaseModel):
    """
    Single data point in usage trend time-series.

    Represents consumption amount during a specific time period.
    Negative values indicate stock additions, positive values indicate removals.
    """

    timestamp: datetime = Field(..., description="Period start timestamp (ISO 8601)")
    consumed: int = Field(
        ...,
        description="Net consumption in period (positive = removed, negative = added)",
    )
    added: int = Field(..., description="Units added to stock in period", ge=0)
    removed: int = Field(..., description="Units removed from stock in period", ge=0)

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "timestamp": "2025-10-16T00:00:00Z",
                "consumed": 15,
                "added": 0,
                "removed": 15,
            }
        }


class UsageTrendsRequest(BaseModel):
    """
    Request schema for usage trend analysis.

    Query parameters for analyzing consumption patterns over time.
    Used to generate bar charts showing usage velocity.

    Examples:
        Daily usage for last 30 days:
            {
                "component_id": "660e8400-e29b-41d4-a716-446655440001",
                "location_id": null,
                "start_date": "2025-09-16T00:00:00Z",
                "end_date": "2025-10-16T00:00:00Z",
                "period": "daily"
            }
    """

    component_id: str = Field(..., description="Component UUID to analyze")
    location_id: str | None = Field(
        None, description="Optional location UUID (null = all locations)"
    )
    start_date: datetime = Field(..., description="Start of date range (ISO 8601)")
    end_date: datetime = Field(..., description="End of date range (ISO 8601)")
    period: AggregationPeriod = Field(
        AggregationPeriod.DAILY,
        description="Time aggregation period (daily, weekly, monthly)",
    )


class UsageTrendsResponse(BaseModel):
    """
    Response schema for usage trend analysis.

    Returns consumption patterns and velocity metrics for a component.
    Designed for Chart.js bar chart and velocity metric display.
    """

    component_id: str = Field(..., description="Component UUID")
    component_name: str = Field(..., description="Component name")
    location_id: str | None = Field(
        None, description="Storage location UUID (null = all locations)"
    )
    location_name: str | None = Field(
        None, description="Storage location name (null = all locations)"
    )
    period: AggregationPeriod = Field(..., description="Time aggregation period used")
    data: list[UsageTrendDataPoint] = Field(
        ..., description="Time-series usage data points"
    )
    velocity: VelocityMetrics = Field(..., description="Consumption velocity metrics")
    metadata: dict = Field(
        ..., description="Additional metadata (date range, analysis notes)"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "component_id": "660e8400-e29b-41d4-a716-446655440001",
                "component_name": "Ceramic Capacitor 100nF 0805",
                "location_id": None,
                "location_name": None,
                "period": "daily",
                "data": [
                    {
                        "timestamp": "2025-10-15T00:00:00Z",
                        "consumed": 10,
                        "added": 0,
                        "removed": 10,
                    },
                    {
                        "timestamp": "2025-10-16T00:00:00Z",
                        "consumed": 15,
                        "added": 0,
                        "removed": 15,
                    },
                ],
                "velocity": {
                    "daily_average": 3.5,
                    "weekly_average": 24.5,
                    "monthly_average": 105.0,
                    "total_consumed": 315,
                    "days_analyzed": 90,
                },
                "metadata": {
                    "start_date": "2025-07-18T00:00:00Z",
                    "end_date": "2025-10-16T00:00:00Z",
                },
            }
        }


# ==================== Forecast Schemas ====================


class ForecastDataPoint(BaseModel):
    """
    Single forecast data point with prediction and confidence.

    Uses simple moving average for prediction. Confidence decreases
    as forecast horizon extends into the future.
    """

    timestamp: datetime = Field(..., description="Forecast timestamp (ISO 8601)")
    predicted_quantity: float = Field(
        ...,
        description="Predicted stock quantity (moving average)",
        ge=0,
    )
    confidence_level: float = Field(
        ...,
        description="Confidence level for this prediction (0.0-1.0, 1.0 = highest)",
        ge=0,
        le=1.0,
    )
    will_trigger_reorder: bool = Field(
        ...,
        description="True if predicted quantity falls below reorder threshold",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "timestamp": "2025-10-23T00:00:00Z",
                "predicted_quantity": 85.5,
                "confidence_level": 0.85,
                "will_trigger_reorder": True,
            }
        }


class ReorderSuggestion(BaseModel):
    """
    Reorder suggestion based on forecast analysis.

    Provides actionable recommendation for restocking including timing
    and quantity based on consumption velocity and lead time.
    """

    should_reorder: bool = Field(
        ..., description="True if reorder is recommended based on forecast"
    )
    suggested_date: datetime | None = Field(
        None,
        description="Suggested date to place reorder (ISO 8601, null if no reorder needed)",
    )
    suggested_quantity: int | None = Field(
        None,
        description="Suggested reorder quantity (null if no reorder needed)",
        ge=0,
    )
    estimated_stockout_date: datetime | None = Field(
        None,
        description="Estimated date when stock will reach zero (ISO 8601, null if no stockout predicted)",
    )
    days_until_stockout: int | None = Field(
        None,
        description="Days until predicted stockout (null if no stockout predicted)",
        ge=0,
    )
    confidence_level: float = Field(
        ...,
        description="Confidence in this suggestion (0.0-1.0)",
        ge=0,
        le=1.0,
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "should_reorder": True,
                "suggested_date": "2025-10-20T00:00:00Z",
                "suggested_quantity": 200,
                "estimated_stockout_date": "2025-11-05T00:00:00Z",
                "days_until_stockout": 20,
                "confidence_level": 0.82,
            }
        }


class ForecastRequest(BaseModel):
    """
    Request schema for stock forecast generation.

    Query parameters for generating moving average forecasts.
    Used to predict future stock levels and reorder timing.

    Examples:
        7-day forecast with 30-day historical basis:
            {
                "component_id": "660e8400-e29b-41d4-a716-446655440001",
                "location_id": "770e8400-e29b-41d4-a716-446655440001",
                "horizon": "7d",
                "lookback_days": 30
            }

        30-day forecast with 90-day historical basis:
            {
                "component_id": "660e8400-e29b-41d4-a716-446655440001",
                "location_id": null,
                "horizon": "30d",
                "lookback_days": 90
            }
    """

    component_id: str = Field(..., description="Component UUID to forecast")
    location_id: str | None = Field(
        None, description="Optional location UUID (null = all locations)"
    )
    horizon: ForecastHorizon = Field(
        ForecastHorizon.TWO_WEEKS,
        description="Forecast horizon (7d, 14d, 30d, 90d)",
    )
    lookback_days: int = Field(
        30,
        description="Number of historical days to use for moving average (7-365)",
        ge=7,
        le=365,
    )


class ForecastResponse(BaseModel):
    """
    Response schema for stock forecast data.

    Returns predicted stock levels using simple moving average algorithm.
    Designed for Chart.js line chart with forecast overlay.

    Includes reorder suggestions based on predicted stockout timing.
    """

    component_id: str = Field(..., description="Component UUID")
    component_name: str = Field(..., description="Component name")
    location_id: str | None = Field(
        None, description="Storage location UUID (null = all locations)"
    )
    location_name: str | None = Field(
        None, description="Storage location name (null = all locations)"
    )
    current_quantity: int = Field(..., description="Current stock quantity", ge=0)
    reorder_threshold: int | None = Field(
        None, description="Reorder threshold (null if not configured)", ge=0
    )
    forecast_horizon: ForecastHorizon = Field(
        ..., description="Forecast time horizon used"
    )
    lookback_days: int = Field(
        ..., description="Historical days analyzed for moving average"
    )
    data: list[ForecastDataPoint] = Field(
        ..., description="Forecast data points (one per day)"
    )
    reorder_suggestion: ReorderSuggestion = Field(
        ..., description="Automated reorder recommendation"
    )
    metadata: dict = Field(
        ...,
        description="Additional metadata (algorithm, confidence notes, velocity)",
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "component_id": "660e8400-e29b-41d4-a716-446655440001",
                "component_name": "Ceramic Capacitor 100nF 0805",
                "location_id": "770e8400-e29b-41d4-a716-446655440001",
                "location_name": "Bin A-12",
                "current_quantity": 120,
                "reorder_threshold": 100,
                "forecast_horizon": "14d",
                "lookback_days": 30,
                "data": [
                    {
                        "timestamp": "2025-10-17T00:00:00Z",
                        "predicted_quantity": 115.5,
                        "confidence_level": 0.95,
                        "will_trigger_reorder": False,
                    },
                    {
                        "timestamp": "2025-10-23T00:00:00Z",
                        "predicted_quantity": 85.5,
                        "confidence_level": 0.85,
                        "will_trigger_reorder": True,
                    },
                ],
                "reorder_suggestion": {
                    "should_reorder": True,
                    "suggested_date": "2025-10-20T00:00:00Z",
                    "suggested_quantity": 200,
                    "estimated_stockout_date": "2025-11-05T00:00:00Z",
                    "days_until_stockout": 20,
                    "confidence_level": 0.82,
                },
                "metadata": {
                    "algorithm": "simple_moving_average",
                    "daily_velocity": 3.5,
                    "notes": "Confidence decreases with forecast horizon",
                },
            }
        }


# ==================== Dashboard Summary Schemas ====================


class ComponentStockSummary(BaseModel):
    """
    Summary statistics for a single component across all locations.

    Used in dashboard cards to show high-level stock health metrics.
    """

    component_id: str = Field(..., description="Component UUID")
    component_name: str = Field(..., description="Component name")
    total_quantity: int = Field(
        ..., description="Total stock across all locations", ge=0
    )
    locations_count: int = Field(..., description="Number of storage locations", ge=0)
    has_active_alerts: bool = Field(
        ..., description="True if component has any active reorder alerts"
    )
    daily_velocity: float = Field(
        ..., description="Average daily consumption (last 30 days)", ge=0
    )
    days_until_stockout: int | None = Field(
        None,
        description="Estimated days until stockout (null if not predicted)",
        ge=0,
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "component_id": "660e8400-e29b-41d4-a716-446655440001",
                "component_name": "Ceramic Capacitor 100nF 0805",
                "total_quantity": 150,
                "locations_count": 2,
                "has_active_alerts": True,
                "daily_velocity": 3.5,
                "days_until_stockout": 20,
            }
        }


class InventoryHealthMetrics(BaseModel):
    """
    Aggregate health metrics for entire inventory.

    Provides dashboard-level KPIs for stock management monitoring.
    """

    total_components: int = Field(
        ..., description="Total number of unique components", ge=0
    )
    low_stock_count: int = Field(
        ..., description="Components with active reorder alerts", ge=0
    )
    out_of_stock_count: int = Field(
        ..., description="Components with zero quantity", ge=0
    )
    total_inventory_value: float = Field(
        ..., description="Total inventory value (all components)", ge=0
    )
    active_alerts_count: int = Field(
        ..., description="Total active reorder alerts", ge=0
    )
    average_stock_velocity: float = Field(
        ...,
        description="Average daily consumption across all components",
        ge=0,
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "total_components": 523,
                "low_stock_count": 42,
                "out_of_stock_count": 5,
                "total_inventory_value": 15432.50,
                "active_alerts_count": 37,
                "average_stock_velocity": 2.3,
            }
        }


class DashboardSummaryRequest(BaseModel):
    """
    Request schema for dashboard summary data.

    Optional filters to constrain dashboard metrics to specific subsets.

    Examples:
        All components:
            {
                "category_id": null,
                "location_id": null
            }

        Specific category only:
            {
                "category_id": "880e8400-e29b-41d4-a716-446655440001",
                "location_id": null
            }
    """

    category_id: str | None = Field(
        None, description="Optional category filter (null = all categories)"
    )
    location_id: str | None = Field(
        None, description="Optional location filter (null = all locations)"
    )


class DashboardSummaryResponse(BaseModel):
    """
    Response schema for analytics dashboard summary.

    Provides aggregated metrics and top components for dashboard display.
    Designed for Quasar cards and Chart.js summary charts.
    """

    health_metrics: InventoryHealthMetrics = Field(
        ..., description="Overall inventory health KPIs"
    )
    top_low_stock: list[ComponentStockSummary] = Field(
        ...,
        description="Top 10 components by shortage urgency (ordered by days until stockout)",
        max_length=10,
    )
    top_consumers: list[ComponentStockSummary] = Field(
        ...,
        description="Top 10 components by daily consumption velocity",
        max_length=10,
    )
    recent_activity_count: int = Field(
        ...,
        description="Number of stock transactions in last 7 days",
        ge=0,
    )
    metadata: dict = Field(
        ..., description="Additional metadata (last updated timestamp, filters applied)"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "health_metrics": {
                    "total_components": 523,
                    "low_stock_count": 42,
                    "out_of_stock_count": 5,
                    "total_inventory_value": 15432.50,
                    "active_alerts_count": 37,
                    "average_stock_velocity": 2.3,
                },
                "top_low_stock": [
                    {
                        "component_id": "660e8400-e29b-41d4-a716-446655440001",
                        "component_name": "Ceramic Capacitor 100nF 0805",
                        "total_quantity": 150,
                        "locations_count": 2,
                        "has_active_alerts": True,
                        "daily_velocity": 3.5,
                        "days_until_stockout": 20,
                    }
                ],
                "top_consumers": [],
                "recent_activity_count": 127,
                "metadata": {
                    "last_updated": "2025-10-16T12:34:56Z",
                    "category_filter": None,
                    "location_filter": None,
                },
            }
        }


# ==================== Slow-Moving Stock Schemas ====================


class SlowMovingItem(BaseModel):
    """
    Component identified as slow-moving based on usage analysis.

    Slow-moving items have low velocity relative to stock quantity,
    indicating potential overstocking or obsolescence.
    """

    component_id: str = Field(..., description="Component UUID")
    component_name: str = Field(..., description="Component name")
    total_quantity: int = Field(..., description="Total stock quantity", ge=0)
    daily_velocity: float = Field(..., description="Average daily consumption", ge=0)
    days_of_stock: float = Field(
        ...,
        description="Days of stock remaining at current velocity (quantity / velocity)",
        ge=0,
    )
    last_used_date: datetime | None = Field(
        None,
        description="Last date component was removed from stock (ISO 8601, null if never used)",
    )
    days_since_last_use: int | None = Field(
        None,
        description="Days since last use (null if never used)",
        ge=0,
    )
    inventory_value: float = Field(
        ..., description="Total inventory value for this component", ge=0
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "component_id": "660e8400-e29b-41d4-a716-446655440001",
                "component_name": "Legacy IC Obsolete Model",
                "total_quantity": 500,
                "daily_velocity": 0.2,
                "days_of_stock": 2500.0,
                "last_used_date": "2024-08-15T00:00:00Z",
                "days_since_last_use": 62,
                "inventory_value": 1250.00,
            }
        }


class SlowMovingStockRequest(BaseModel):
    """
    Request schema for slow-moving stock analysis.

    Query parameters for identifying components with low consumption velocity.

    Examples:
        Identify slow movers (>180 days of stock):
            {
                "min_days_of_stock": 180,
                "min_days_since_last_use": 60
            }

        Find potential obsolete stock:
            {
                "min_days_of_stock": 365,
                "min_days_since_last_use": 180
            }
    """

    min_days_of_stock: int = Field(
        180,
        description="Minimum days of stock to classify as slow-moving (default 180)",
        ge=1,
    )
    min_days_since_last_use: int | None = Field(
        None,
        description="Optional minimum days since last use filter",
        ge=0,
    )


class SlowMovingStockResponse(BaseModel):
    """
    Response schema for slow-moving stock analysis.

    Returns list of components with low consumption velocity relative to
    current stock levels. Useful for identifying overstocking and obsolescence.
    """

    items: list[SlowMovingItem] = Field(
        ...,
        description="List of slow-moving components (ordered by days_of_stock DESC)",
    )
    total_count: int = Field(
        ..., description="Total number of slow-moving items found", ge=0
    )
    total_value_locked: float = Field(
        ...,
        description="Total inventory value tied up in slow-moving stock",
        ge=0,
    )
    metadata: dict = Field(
        ..., description="Additional metadata (analysis parameters, date range)"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "items": [
                    {
                        "component_id": "660e8400-e29b-41d4-a716-446655440001",
                        "component_name": "Legacy IC Obsolete Model",
                        "total_quantity": 500,
                        "daily_velocity": 0.2,
                        "days_of_stock": 2500.0,
                        "last_used_date": "2024-08-15T00:00:00Z",
                        "days_since_last_use": 62,
                        "inventory_value": 1250.00,
                    }
                ],
                "total_count": 1,
                "total_value_locked": 1250.00,
                "metadata": {
                    "min_days_of_stock": 180,
                    "min_days_since_last_use": None,
                    "analysis_date": "2025-10-16T00:00:00Z",
                },
            }
        }
