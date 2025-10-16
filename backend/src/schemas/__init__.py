"""
Pydantic schemas for PartsHub API.
"""

from .analytics import (
    AggregationPeriod,
    ComponentStockSummary,
    DashboardSummaryRequest,
    DashboardSummaryResponse,
    DateRangeFilter,
    ForecastDataPoint,
    ForecastHorizon,
    ForecastRequest,
    ForecastResponse,
    InventoryHealthMetrics,
    ReorderSuggestion,
    SlowMovingItem,
    SlowMovingStockRequest,
    SlowMovingStockResponse,
    StockDataPoint,
    StockLevelsRequest,
    StockLevelsResponse,
    UsageTrendDataPoint,
    UsageTrendsRequest,
    UsageTrendsResponse,
    VelocityMetrics,
)
from .stock_operations import (
    AddStockRequest,
    AddStockResponse,
    MoveStockRequest,
    MoveStockResponse,
    RemoveStockRequest,
    RemoveStockResponse,
    StockHistoryEntry,
)

__all__ = [
    # Stock operations schemas
    "AddStockRequest",
    "AddStockResponse",
    "RemoveStockRequest",
    "RemoveStockResponse",
    "MoveStockRequest",
    "MoveStockResponse",
    "StockHistoryEntry",
    # Analytics schemas - Enums
    "AggregationPeriod",
    "ForecastHorizon",
    # Analytics schemas - Base/Common
    "DateRangeFilter",
    # Analytics schemas - Stock Time-Series
    "StockDataPoint",
    "StockLevelsRequest",
    "StockLevelsResponse",
    # Analytics schemas - Usage Trends
    "VelocityMetrics",
    "UsageTrendDataPoint",
    "UsageTrendsRequest",
    "UsageTrendsResponse",
    # Analytics schemas - Forecast
    "ForecastDataPoint",
    "ReorderSuggestion",
    "ForecastRequest",
    "ForecastResponse",
    # Analytics schemas - Dashboard Summary
    "ComponentStockSummary",
    "InventoryHealthMetrics",
    "DashboardSummaryRequest",
    "DashboardSummaryResponse",
    # Analytics schemas - Slow-Moving Stock
    "SlowMovingItem",
    "SlowMovingStockRequest",
    "SlowMovingStockResponse",
]
