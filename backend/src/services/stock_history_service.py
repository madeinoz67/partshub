"""
Stock history service for pagination and export functionality.

This service provides:
- Paginated stock history retrieval with sorting
- Multi-format export (CSV, Excel/XLSX, JSON)

Implements FR-043 through FR-048 and FR-059 from spec.md.
"""

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any, Literal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from ..models import Component, StockTransaction

logger = logging.getLogger(__name__)


class StockHistoryService:
    """
    Service for stock history pagination and export operations.

    Implements FR-043 (history columns), FR-044 (sorting), FR-045 (history refresh),
    FR-046 (export access), FR-047 (pagination), FR-048 (default page size),
    and FR-059 (export formats) from spec.md.
    """

    def __init__(self, session: Session):
        """
        Initialize service with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def get_paginated_history(
        self,
        component_id: str,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "created_at",
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> dict[str, Any]:
        """
        Get paginated stock transaction history for a component.

        Implements pagination with sorting support per FR-044, FR-047, FR-048.
        Returns 10 entries per page by default (FR-048).

        Args:
            component_id: UUID of component
            page: Page number (1-indexed)
            page_size: Number of entries per page (default 10)
            sort_by: Field to sort by (created_at, quantity_change, transaction_type, user_name)
            sort_order: Sort order (asc or desc)

        Returns:
            Dict containing:
                - entries: List of StockTransaction objects with location names
                - pagination: Metadata (page, page_size, total_entries, total_pages, has_next, has_previous)

        Raises:
            HTTPException(404): Component not found
            HTTPException(400): Invalid sort_by field or pagination parameters
        """
        # Validate component exists
        component = self.session.get(Component, component_id)
        if not component:
            raise HTTPException(status_code=404, detail="Component not found")

        # Validate pagination parameters
        if page < 1:
            raise HTTPException(status_code=400, detail="Page number must be >= 1")
        if page_size < 1 or page_size > 100:
            raise HTTPException(
                status_code=400, detail="Page size must be between 1 and 100"
            )

        # Validate and map sort_by field
        sort_field_map = {
            "created_at": StockTransaction.created_at,
            "quantity_change": StockTransaction.quantity_change,
            "transaction_type": StockTransaction.transaction_type,
            "user_name": StockTransaction.user_name,
        }

        if sort_by not in sort_field_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_by field. Must be one of: {', '.join(sort_field_map.keys())}",
            )

        # Build base query with eager loading for relationships
        query = (
            select(StockTransaction)
            .where(StockTransaction.component_id == component_id)
            .options(
                joinedload(StockTransaction.from_location),
                joinedload(StockTransaction.to_location),
            )
        )

        # Apply sorting
        sort_column = sort_field_map[sort_by]
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Get total count for pagination metadata
        count_query = select(StockTransaction).where(
            StockTransaction.component_id == component_id
        )
        total_count = len(self.session.execute(count_query).scalars().all())

        # Calculate pagination
        total_pages = (
            (total_count + page_size - 1) // page_size if total_count > 0 else 0
        )
        has_next = page < total_pages
        has_previous = page > 1

        # Apply pagination (LIMIT/OFFSET)
        offset = (page - 1) * page_size
        query = query.limit(page_size).offset(offset)

        # Execute query
        transactions = self.session.execute(query).scalars().all()

        # Build response
        return {
            "entries": list(transactions),
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_entries": total_count,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_previous": has_previous,
            },
        }

    def export_history(
        self,
        component_id: str,
        export_format: Literal["csv", "xlsx", "json"],
        sort_by: str = "created_at",
        sort_order: Literal["asc", "desc"] = "desc",
    ) -> tuple[bytes | str, str, str]:
        """
        Export complete stock transaction history in specified format.

        Implements FR-043 (column headers), FR-059 (export formats).
        Exports ALL history entries without pagination.

        Args:
            component_id: UUID of component
            export_format: Export format (csv, xlsx, json)
            sort_by: Field to sort by
            sort_order: Sort order (asc or desc)

        Returns:
            Tuple of (content, content_type, filename):
                - content: Bytes (xlsx) or string (csv/json)
                - content_type: MIME type
                - filename: Suggested filename with extension

        Raises:
            HTTPException(404): Component not found
            HTTPException(400): Invalid format or sort parameters
        """
        # Validate component exists
        component = self.session.get(Component, component_id)
        if not component:
            raise HTTPException(status_code=404, detail="Component not found")

        # Validate format
        if export_format not in ["csv", "xlsx", "json"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid format. Must be one of: csv, xlsx, json",
            )

        # Validate and map sort_by field
        sort_field_map = {
            "created_at": StockTransaction.created_at,
            "quantity_change": StockTransaction.quantity_change,
            "transaction_type": StockTransaction.transaction_type,
            "user_name": StockTransaction.user_name,
        }

        if sort_by not in sort_field_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_by field. Must be one of: {', '.join(sort_field_map.keys())}",
            )

        # Build query with eager loading
        query = (
            select(StockTransaction)
            .where(StockTransaction.component_id == component_id)
            .options(
                joinedload(StockTransaction.from_location),
                joinedload(StockTransaction.to_location),
            )
        )

        # Apply sorting
        sort_column = sort_field_map[sort_by]
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Get all transactions (no pagination)
        transactions = self.session.execute(query).scalars().all()

        # Generate timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        component_name = component.name.replace(" ", "_").replace("/", "_")

        # Export based on format
        if export_format == "csv":
            content = self._export_to_csv(transactions)
            content_type = "text/csv"
            filename = f"stock_history_{component_name}_{timestamp}.csv"
        elif export_format == "xlsx":
            content = self._export_to_xlsx(transactions)
            content_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            filename = f"stock_history_{component_name}_{timestamp}.xlsx"
        else:  # json
            content = self._export_to_json(component, transactions)
            content_type = "application/json"
            filename = f"stock_history_{component_name}_{timestamp}.json"

        return content, content_type, filename

    def _export_to_csv(self, transactions: list[StockTransaction]) -> str:
        """
        Export transactions to CSV format.

        Column headers per FR-043: Date, Type, Quantity Change, Previous Qty,
        New Qty, From Location, To Location, Lot ID, Price/Unit, Total Price,
        User, Reason, Notes

        Args:
            transactions: List of StockTransaction objects

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write headers (FR-043)
        writer.writerow(
            [
                "Date",
                "Type",
                "Quantity Change",
                "Previous Qty",
                "New Qty",
                "From Location",
                "To Location",
                "Lot ID",
                "Price/Unit",
                "Total Price",
                "User",
                "Reason",
                "Notes",
            ]
        )

        # Write data rows
        for txn in transactions:
            # Format quantity change with +/- indicator
            qty_change = txn.quantity_change
            qty_str = f"{'+' if qty_change > 0 else ''}{qty_change}"

            # Get location names
            from_loc = txn.from_location.name if txn.from_location else ""
            to_loc = txn.to_location.name if txn.to_location else ""

            # Format pricing
            price_per_unit = (
                f"${float(txn.price_per_unit):.2f}" if txn.price_per_unit else ""
            )
            total_price = f"${float(txn.total_price):.2f}" if txn.total_price else ""

            writer.writerow(
                [
                    txn.created_at.isoformat() if txn.created_at else "",
                    txn.transaction_type.value.upper(),
                    qty_str,
                    txn.previous_quantity,
                    txn.new_quantity,
                    from_loc,
                    to_loc,
                    txn.lot_id or "",
                    price_per_unit,
                    total_price,
                    txn.user_name or "",
                    txn.reason or "",
                    txn.notes or "",
                ]
            )

        return output.getvalue()

    def _export_to_xlsx(self, transactions: list[StockTransaction]) -> bytes:
        """
        Export transactions to Excel/XLSX format using openpyxl.

        Args:
            transactions: List of StockTransaction objects

        Returns:
            XLSX file as bytes
        """
        try:
            from openpyxl import Workbook
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Excel export not available. openpyxl library not installed.",
            )

        wb = Workbook()
        ws = wb.active
        ws.title = "Stock History"

        # Write headers (same as CSV, per FR-043)
        ws.append(
            [
                "Date",
                "Type",
                "Quantity Change",
                "Previous Qty",
                "New Qty",
                "From Location",
                "To Location",
                "Lot ID",
                "Price/Unit",
                "Total Price",
                "User",
                "Reason",
                "Notes",
            ]
        )

        # Write data rows
        for txn in transactions:
            # Format quantity change with +/- indicator
            qty_change = txn.quantity_change
            qty_str = f"{'+' if qty_change > 0 else ''}{qty_change}"

            # Get location names
            from_loc = txn.from_location.name if txn.from_location else ""
            to_loc = txn.to_location.name if txn.to_location else ""

            # Format pricing (Excel can handle numbers directly)
            price_per_unit = float(txn.price_per_unit) if txn.price_per_unit else ""
            total_price = float(txn.total_price) if txn.total_price else ""

            ws.append(
                [
                    txn.created_at.isoformat() if txn.created_at else "",
                    txn.transaction_type.value.upper(),
                    qty_str,
                    txn.previous_quantity,
                    txn.new_quantity,
                    from_loc,
                    to_loc,
                    txn.lot_id or "",
                    price_per_unit,
                    total_price,
                    txn.user_name or "",
                    txn.reason or "",
                    txn.notes or "",
                ]
            )

        # Save to bytes
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output.getvalue()

    def _export_to_json(
        self, component: Component, transactions: list[StockTransaction]
    ) -> str:
        """
        Export transactions to JSON format.

        Includes component metadata and full transaction details.

        Args:
            component: Component object
            transactions: List of StockTransaction objects

        Returns:
            JSON string
        """
        # Build entries list
        entries = []
        for txn in transactions:
            entry = {
                "id": txn.id,
                "created_at": txn.created_at.isoformat() if txn.created_at else None,
                "transaction_type": txn.transaction_type.value.upper(),
                "quantity_change": txn.quantity_change,
                "previous_quantity": txn.previous_quantity,
                "new_quantity": txn.new_quantity,
                "from_location_id": txn.from_location_id,
                "from_location_name": (
                    txn.from_location.name if txn.from_location else None
                ),
                "to_location_id": txn.to_location_id,
                "to_location_name": txn.to_location.name if txn.to_location else None,
                "lot_id": txn.lot_id,
                "price_per_unit": (
                    float(txn.price_per_unit) if txn.price_per_unit else None
                ),
                "total_price": float(txn.total_price) if txn.total_price else None,
                "user_id": txn.user_id,
                "user_name": txn.user_name,
                "reason": txn.reason,
                "notes": txn.notes,
            }
            entries.append(entry)

        # Build response object matching ExportResponse schema
        response = {
            "component_id": component.id,
            "component_name": component.name,
            "exported_at": datetime.now().isoformat(),
            "total_entries": len(entries),
            "entries": entries,
        }

        return json.dumps(response, indent=2)
