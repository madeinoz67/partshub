"""
Analytics API endpoints for stock analytics and forecasting.

Provides REST API for stock analytics and inventory insights:
- GET /api/v1/analytics/stock-levels - Time-series stock level data
- GET /api/v1/analytics/usage-trends - Consumption patterns and velocity
- GET /api/v1/analytics/forecast - Stock predictions with reorder suggestions
- GET /api/v1/analytics/dashboard - Inventory KPIs and top lists
- GET /api/v1/analytics/slow-moving-stock - Identify slow-moving/obsolete stock

All endpoints require admin authentication. Designed for Chart.js visualization
in Vue.js frontend with comprehensive time-series and forecasting capabilities.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..auth.dependencies import require_admin
from ..database import get_db
from ..schemas.analytics import (
    AggregationPeriod,
    DashboardSummaryResponse,
    ForecastHorizon,
    ForecastResponse,
    SlowMovingStockResponse,
    StockLevelsResponse,
    UsageTrendsResponse,
)
from ..services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


# ==================== Stock Time-Series ====================


@router.get(
    "/stock-levels",
    response_model=StockLevelsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get stock level time-series",
    description=(
        "Returns historical stock levels aggregated by time period. "
        "Used for Chart.js line chart visualization of stock trends over time. "
        "Supports daily, weekly, and monthly aggregation."
    ),
)
async def get_stock_levels(
    component_id: UUID = Query(..., description="Component UUID to analyze"),
    location_id: UUID | None = Query(
        None, description="Optional storage location UUID (null = all locations)"
    ),
    start_date: datetime = Query(..., description="Start of date range (ISO 8601)"),
    end_date: datetime = Query(..., description="End of date range (ISO 8601)"),
    period: AggregationPeriod = Query(
        AggregationPeriod.DAILY,
        description="Time aggregation period (daily, weekly, monthly)",
    ),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> StockLevelsResponse:
    """
    Get time-series stock level data for a component.

    Calculates running stock totals over time by analyzing historical
    stock transactions. Data is aggregated by the requested time period
    for optimal chart rendering.

    **Admin-only operation.**

    Args:
        component_id: Component UUID to analyze
        location_id: Optional location filter (None = aggregate all locations)
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        period: Aggregation period (daily, weekly, monthly)
        db: Database session (injected)
        admin: Current admin user (injected)

    Returns:
        StockLevelsResponse with time-series data and metadata

    Raises:
        HTTPException 403: User is not admin
        HTTPException 404: Component or location not found

    Example:
        GET /api/v1/analytics/stock-levels?component_id=123&start_date=2025-01-01T00:00:00Z&end_date=2025-10-17T00:00:00Z&period=daily
    """
    service = AnalyticsService(db)
    return service.get_stock_levels(
        component_id=str(component_id),
        location_id=str(location_id) if location_id else None,
        start_date=start_date,
        end_date=end_date,
        period=period,
    )


# ==================== Usage Trends ====================


@router.get(
    "/usage-trends",
    response_model=UsageTrendsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get usage trends and velocity metrics",
    description=(
        "Analyzes consumption patterns over time with velocity calculations. "
        "Used for Chart.js bar chart showing stock additions vs. removals. "
        "Includes daily/weekly/monthly consumption velocity metrics."
    ),
)
async def get_usage_trends(
    component_id: UUID = Query(..., description="Component UUID to analyze"),
    location_id: UUID | None = Query(
        None, description="Optional storage location UUID (null = all locations)"
    ),
    start_date: datetime = Query(..., description="Start of date range (ISO 8601)"),
    end_date: datetime = Query(..., description="End of date range (ISO 8601)"),
    period: AggregationPeriod = Query(
        AggregationPeriod.DAILY,
        description="Time aggregation period (daily, weekly, monthly)",
    ),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> UsageTrendsResponse:
    """
    Get usage trend analysis with consumption velocity metrics.

    Analyzes stock additions and removals over time, calculating consumption
    velocity (units/day, units/week, units/month). Useful for identifying
    usage patterns and predicting future consumption.

    **Admin-only operation.**

    Args:
        component_id: Component UUID to analyze
        location_id: Optional location filter (None = aggregate all locations)
        start_date: Start of date range (inclusive)
        end_date: End of date range (inclusive)
        period: Aggregation period (daily, weekly, monthly)
        db: Database session (injected)
        admin: Current admin user (injected)

    Returns:
        UsageTrendsResponse with trend data and velocity metrics

    Raises:
        HTTPException 403: User is not admin
        HTTPException 404: Component not found

    Example:
        GET /api/v1/analytics/usage-trends?component_id=123&start_date=2025-09-01T00:00:00Z&end_date=2025-10-17T00:00:00Z&period=weekly
    """
    service = AnalyticsService(db)
    return service.get_usage_trends(
        component_id=str(component_id),
        location_id=str(location_id) if location_id else None,
        start_date=start_date,
        end_date=end_date,
        period=period,
    )


# ==================== Stock Forecasting ====================


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Get stock forecast with reorder suggestions",
    description=(
        "Generates moving average forecast predicting future stock levels. "
        "Includes confidence levels and automated reorder suggestions. "
        "Used for Chart.js forecast overlay with prediction intervals."
    ),
)
async def get_forecast(
    component_id: UUID = Query(..., description="Component UUID to forecast"),
    location_id: UUID | None = Query(
        None, description="Optional storage location UUID (null = all locations)"
    ),
    horizon: ForecastHorizon = Query(
        ForecastHorizon.TWO_WEEKS,
        description="Forecast time horizon (7d, 14d, 30d, 90d)",
    ),
    lookback_days: int = Query(
        30,
        ge=7,
        le=365,
        description="Number of historical days to analyze for moving average",
    ),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> ForecastResponse:
    """
    Generate stock forecast using moving average algorithm.

    Predicts future stock levels based on historical consumption patterns.
    Includes confidence levels (decreasing with horizon distance) and
    automated reorder suggestions when stock is predicted to fall below
    reorder threshold.

    **Admin-only operation.**

    Args:
        component_id: Component UUID to forecast
        location_id: Optional location filter (None = aggregate all locations)
        horizon: Forecast time horizon (7d, 14d, 30d, 90d)
        lookback_days: Historical days to analyze (7-365)
        db: Database session (injected)
        admin: Current admin user (injected)

    Returns:
        ForecastResponse with predictions and reorder suggestions

    Raises:
        HTTPException 403: User is not admin
        HTTPException 404: Component not found

    Example:
        GET /api/v1/analytics/forecast?component_id=123&horizon=14d&lookback_days=30
    """
    service = AnalyticsService(db)
    return service.get_forecast(
        component_id=str(component_id),
        location_id=str(location_id) if location_id else None,
        horizon=horizon,
        lookback_days=lookback_days,
    )


# ==================== Dashboard Summary ====================


@router.get(
    "/dashboard",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get dashboard summary with inventory KPIs",
    description=(
        "Returns aggregated inventory health metrics, top low-stock components, "
        "and top consumers. Used for analytics dashboard cards and summary views. "
        "Supports optional category and location filtering."
    ),
)
async def get_dashboard_summary(
    category_id: UUID | None = Query(
        None, description="Optional category filter (null = all categories)"
    ),
    location_id: UUID | None = Query(
        None, description="Optional storage location filter (null = all locations)"
    ),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> DashboardSummaryResponse:
    """
    Get dashboard summary with inventory health metrics and top lists.

    Provides high-level KPIs including:
    - Total components count
    - Low stock / out of stock counts
    - Total inventory value
    - Average consumption velocity
    - Top 10 components by shortage urgency
    - Top 10 components by consumption velocity
    - Recent activity count (last 7 days)

    **Admin-only operation.**

    Args:
        category_id: Optional category filter
        location_id: Optional location filter
        db: Database session (injected)
        admin: Current admin user (injected)

    Returns:
        DashboardSummaryResponse with health metrics and top lists

    Raises:
        HTTPException 403: User is not admin

    Example:
        GET /api/v1/analytics/dashboard
        GET /api/v1/analytics/dashboard?category_id=456&location_id=789
    """
    service = AnalyticsService(db)
    return service.get_dashboard_summary(
        category_id=str(category_id) if category_id else None,
        location_id=str(location_id) if location_id else None,
    )


# ==================== Slow-Moving Stock Analysis ====================


@router.get(
    "/slow-moving-stock",
    response_model=SlowMovingStockResponse,
    status_code=status.HTTP_200_OK,
    summary="Identify slow-moving and obsolete stock",
    description=(
        "Identifies components with low consumption velocity relative to stock levels. "
        "Used for finding overstocked or obsolete components. "
        "Calculates tied-up inventory value for capital optimization."
    ),
)
async def get_slow_moving_stock(
    min_days_of_stock: int = Query(
        180,
        ge=1,
        description="Minimum days of stock to classify as slow-moving (default 180)",
    ),
    min_days_since_last_use: int | None = Query(
        None, ge=0, description="Optional minimum days since last use filter"
    ),
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
) -> SlowMovingStockResponse:
    """
    Identify slow-moving and potentially obsolete stock.

    Finds components where current stock quantity represents more than
    a specified number of days of supply based on consumption velocity.
    Useful for:
    - Identifying overstocking issues
    - Finding obsolete components
    - Calculating capital tied up in slow-moving inventory
    - Making procurement decisions

    **Admin-only operation.**

    Args:
        min_days_of_stock: Minimum days of stock to classify as slow-moving (default 180)
        min_days_since_last_use: Optional filter for days since last use
        db: Database session (injected)
        admin: Current admin user (injected)

    Returns:
        SlowMovingStockResponse with slow-moving items and total value locked

    Raises:
        HTTPException 403: User is not admin

    Example:
        GET /api/v1/analytics/slow-moving-stock?min_days_of_stock=180
        GET /api/v1/analytics/slow-moving-stock?min_days_of_stock=365&min_days_since_last_use=90
    """
    service = AnalyticsService(db)
    return service.get_slow_moving_stock(
        min_days_of_stock=min_days_of_stock,
        min_days_since_last_use=min_days_since_last_use,
    )
