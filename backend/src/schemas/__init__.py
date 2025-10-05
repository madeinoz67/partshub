"""
Pydantic schemas for PartsHub API.
"""

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
    "AddStockRequest",
    "AddStockResponse",
    "RemoveStockRequest",
    "RemoveStockResponse",
    "MoveStockRequest",
    "MoveStockResponse",
    "StockHistoryEntry",
]
