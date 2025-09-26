"""
StockService for advanced inventory transactions and history tracking.
Provides enhanced stock management operations beyond basic CRUD.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, func, desc, text
from datetime import datetime, timedelta
from ..models import Component, StockTransaction, TransactionType, Project, ProjectComponent
import uuid
import logging

logger = logging.getLogger(__name__)


class StockService:
    """Advanced service for inventory transactions and stock history analysis."""

    def __init__(self, db: Session):
        self.db = db

    def bulk_stock_update(
        self,
        updates: List[Dict[str, Any]],
        reason: str = "Bulk stock update"
    ) -> Dict[str, Any]:
        """
        Perform bulk stock updates across multiple components.

        Args:
            updates: List of {component_id, quantity_change, transaction_type}
            reason: Reason for bulk update

        Returns:
            Summary of operations performed
        """
        successful_updates = 0
        failed_updates = []
        total_value_change = 0.0

        for update in updates:
            try:
                component_id = update["component_id"]
                quantity_change = update["quantity_change"]
                transaction_type = update["transaction_type"]

                component = self.db.query(Component).filter(Component.id == component_id).first()
                if not component:
                    failed_updates.append({
                        "component_id": component_id,
                        "error": "Component not found"
                    })
                    continue

                # Validate transaction
                if transaction_type == "remove" and component.quantity_on_hand + quantity_change < 0:
                    failed_updates.append({
                        "component_id": component_id,
                        "error": f"Insufficient stock: {component.quantity_on_hand} available"
                    })
                    continue

                # Create transaction
                previous_quantity = component.quantity_on_hand

                if transaction_type == "add":
                    transaction = StockTransaction.create_add_transaction(
                        component=component,
                        quantity=abs(quantity_change),
                        reason=reason
                    )
                    component.quantity_on_hand += abs(quantity_change)
                    if component.average_purchase_price:
                        total_value_change += abs(quantity_change) * component.average_purchase_price

                elif transaction_type == "remove":
                    transaction = StockTransaction.create_remove_transaction(
                        component=component,
                        quantity=abs(quantity_change),
                        reason=reason
                    )
                    component.quantity_on_hand -= abs(quantity_change)
                    if component.average_purchase_price:
                        total_value_change -= abs(quantity_change) * component.average_purchase_price

                elif transaction_type == "adjust":
                    new_quantity = previous_quantity + quantity_change
                    transaction = StockTransaction.create_adjustment_transaction(
                        component=component,
                        new_quantity=new_quantity,
                        reason=reason
                    )
                    component.quantity_on_hand = new_quantity

                else:
                    failed_updates.append({
                        "component_id": component_id,
                        "error": f"Invalid transaction type: {transaction_type}"
                    })
                    continue

                transaction.new_quantity = component.quantity_on_hand
                self.db.add(transaction)
                successful_updates += 1

            except Exception as e:
                failed_updates.append({
                    "component_id": update.get("component_id", "unknown"),
                    "error": str(e)
                })

        self.db.commit()

        return {
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "total_failed": len(failed_updates),
            "estimated_value_change": total_value_change
        }

    def get_stock_movements(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None,
        component_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[StockTransaction]:
        """Get stock movements with filtering."""
        query = (
            self.db.query(StockTransaction)
            .options(selectinload(StockTransaction.component))
            .order_by(desc(StockTransaction.created_at))
        )

        # Apply filters
        if start_date:
            query = query.filter(StockTransaction.created_at >= start_date)

        if end_date:
            query = query.filter(StockTransaction.created_at <= end_date)

        if transaction_type:
            query = query.filter(StockTransaction.transaction_type == transaction_type)

        if component_id:
            query = query.filter(StockTransaction.component_id == component_id)

        # Apply pagination
        query = query.offset(offset).limit(limit)

        return query.all()

    def get_inventory_valuation(
        self,
        category_id: Optional[str] = None,
        storage_location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Calculate current inventory valuation."""
        query = self.db.query(
            func.sum(Component.quantity_on_hand * Component.average_purchase_price).label('total_value'),
            func.sum(Component.quantity_on_hand).label('total_quantity'),
            func.count(Component.id).label('total_components')
        )

        # Apply filters
        if category_id:
            query = query.filter(Component.category_id == category_id)

        if storage_location_id:
            query = query.filter(Component.storage_location_id == storage_location_id)

        result = query.first()

        return {
            "total_value": float(result.total_value) if result.total_value else 0.0,
            "total_quantity": int(result.total_quantity) if result.total_quantity else 0,
            "total_components": int(result.total_components) if result.total_components else 0,
            "average_value_per_component": (
                float(result.total_value) / int(result.total_components)
                if result.total_value and result.total_components
                else 0.0
            )
        }

    def get_stock_alerts(self) -> Dict[str, List[Component]]:
        """Get components requiring stock attention."""
        # Low stock components
        low_stock = (
            self.db.query(Component)
            .options(selectinload(Component.storage_location))
            .filter(Component.quantity_on_hand <= Component.minimum_stock)
            .filter(Component.minimum_stock > 0)
            .order_by(
                (Component.quantity_on_hand / func.nullif(Component.minimum_stock, 0))
            )
            .limit(50)
            .all()
        )

        # Out of stock components
        out_of_stock = (
            self.db.query(Component)
            .options(selectinload(Component.storage_location))
            .filter(Component.quantity_on_hand == 0)
            .filter(Component.minimum_stock > 0)
            .order_by(Component.updated_at.desc())
            .limit(50)
            .all()
        )

        # Overstock components (more than 10x minimum stock)
        overstock = (
            self.db.query(Component)
            .options(selectinload(Component.storage_location))
            .filter(Component.quantity_on_hand > Component.minimum_stock * 10)
            .filter(Component.minimum_stock > 0)
            .order_by(
                (Component.quantity_on_hand / func.nullif(Component.minimum_stock, 0)).desc()
            )
            .limit(50)
            .all()
        )

        return {
            "low_stock": low_stock,
            "out_of_stock": out_of_stock,
            "overstock": overstock
        }

    def analyze_stock_trends(
        self,
        component_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Analyze stock movement trends for a component."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Get transactions in date range
        transactions = (
            self.db.query(StockTransaction)
            .filter(StockTransaction.component_id == component_id)
            .filter(StockTransaction.created_at >= start_date)
            .order_by(StockTransaction.created_at)
            .all()
        )

        if not transactions:
            return {
                "component_id": component_id,
                "period_days": days,
                "total_transactions": 0,
                "net_change": 0,
                "average_daily_change": 0.0,
                "most_common_reason": None
            }

        # Calculate metrics
        total_added = sum(
            t.quantity_change for t in transactions
            if t.transaction_type == TransactionType.ADD
        )
        total_removed = sum(
            t.quantity_change for t in transactions
            if t.transaction_type == TransactionType.REMOVE
        )
        net_change = total_added - total_removed

        # Find most common transaction reason
        reason_counts = {}
        for transaction in transactions:
            reason = transaction.reason or "Unknown"
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

        most_common_reason = max(reason_counts.items(), key=lambda x: x[1])[0] if reason_counts else None

        return {
            "component_id": component_id,
            "period_days": days,
            "total_transactions": len(transactions),
            "total_added": total_added,
            "total_removed": total_removed,
            "net_change": net_change,
            "average_daily_change": net_change / days,
            "most_common_reason": most_common_reason,
            "transaction_reasons": reason_counts
        }

    def predict_stock_needs(
        self,
        component_id: str,
        days_ahead: int = 30,
        confidence_level: float = 0.8
    ) -> Dict[str, Any]:
        """Predict when component will reach low stock based on usage trends."""
        component = self.db.query(Component).filter(Component.id == component_id).first()
        if not component:
            return {"error": "Component not found"}

        # Analyze recent usage (last 90 days)
        trend_data = self.analyze_stock_trends(component_id, days=90)

        if trend_data["total_transactions"] < 3:
            return {
                "component_id": component_id,
                "prediction": "insufficient_data",
                "message": "Not enough transaction history for prediction"
            }

        daily_usage = abs(trend_data["average_daily_change"])
        current_stock = component.quantity_on_hand
        minimum_stock = component.minimum_stock or 0

        if daily_usage <= 0:
            return {
                "component_id": component_id,
                "prediction": "stable",
                "message": "No significant usage trend detected"
            }

        # Calculate days until low stock
        days_until_low_stock = (current_stock - minimum_stock) / daily_usage

        # Prediction confidence based on transaction consistency
        transaction_variance = self._calculate_usage_variance(component_id)
        confidence = max(0.1, min(1.0, confidence_level - transaction_variance))

        prediction_status = "healthy"
        if days_until_low_stock <= 7:
            prediction_status = "critical"
        elif days_until_low_stock <= 30:
            prediction_status = "warning"

        return {
            "component_id": component_id,
            "current_stock": current_stock,
            "minimum_stock": minimum_stock,
            "daily_usage_rate": daily_usage,
            "days_until_low_stock": max(0, days_until_low_stock),
            "prediction_status": prediction_status,
            "confidence": confidence,
            "recommended_reorder_date": (
                datetime.utcnow() + timedelta(days=max(0, days_until_low_stock - 7))
            ).isoformat() if days_until_low_stock > 7 else None
        }

    def _calculate_usage_variance(self, component_id: str) -> float:
        """Calculate variance in component usage to determine prediction confidence."""
        # Get recent transactions
        recent_transactions = (
            self.db.query(StockTransaction)
            .filter(StockTransaction.component_id == component_id)
            .filter(StockTransaction.transaction_type.in_([TransactionType.ADD, TransactionType.REMOVE]))
            .order_by(desc(StockTransaction.created_at))
            .limit(10)
            .all()
        )

        if len(recent_transactions) < 3:
            return 1.0  # High variance, low confidence

        # Calculate variance in transaction sizes
        quantities = [abs(t.quantity_change) for t in recent_transactions]
        if not quantities:
            return 1.0

        mean_quantity = sum(quantities) / len(quantities)
        variance = sum((q - mean_quantity) ** 2 for q in quantities) / len(quantities)

        # Normalize variance (0-1 scale)
        normalized_variance = min(1.0, variance / (mean_quantity ** 2) if mean_quantity > 0 else 1.0)

        return normalized_variance

    def generate_stock_report(
        self,
        include_trends: bool = True,
        include_predictions: bool = False
    ) -> Dict[str, Any]:
        """Generate comprehensive stock analysis report."""
        # Basic inventory statistics
        inventory_stats = self.get_inventory_valuation()

        # Stock alerts
        alerts = self.get_stock_alerts()

        # Recent stock movements (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_movements = self.get_stock_movements(
            start_date=week_ago,
            limit=50
        )

        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "inventory_valuation": inventory_stats,
            "stock_alerts": {
                "low_stock_count": len(alerts["low_stock"]),
                "out_of_stock_count": len(alerts["out_of_stock"]),
                "overstock_count": len(alerts["overstock"])
            },
            "recent_activity": {
                "transactions_last_week": len(recent_movements),
                "most_active_components": self._get_most_active_components()
            }
        }

        if include_trends:
            report["trending_components"] = self._get_trending_components()

        if include_predictions:
            report["stock_predictions"] = self._get_stock_predictions()

        return report

    def _get_most_active_components(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get components with most recent stock activity."""
        week_ago = datetime.utcnow() - timedelta(days=7)

        # Query for most active components
        result = (
            self.db.query(
                StockTransaction.component_id,
                func.count(StockTransaction.id).label('transaction_count'),
                func.sum(func.abs(StockTransaction.quantity_change)).label('total_quantity')
            )
            .filter(StockTransaction.created_at >= week_ago)
            .group_by(StockTransaction.component_id)
            .order_by(func.count(StockTransaction.id).desc())
            .limit(limit)
            .all()
        )

        # Get component details
        active_components = []
        for component_id, transaction_count, total_quantity in result:
            component = self.db.query(Component).filter(Component.id == component_id).first()
            if component:
                active_components.append({
                    "component_id": component_id,
                    "part_number": component.part_number,
                    "name": component.name,
                    "transaction_count": transaction_count,
                    "total_quantity_moved": int(total_quantity or 0)
                })

        return active_components

    def _get_trending_components(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get components with significant usage trends."""
        # This would need more sophisticated analysis
        # For now, return components with highest recent activity variance
        return []

    def _get_stock_predictions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get stock predictions for critical components."""
        # Get components with low stock that have sufficient transaction history
        low_stock_components = (
            self.db.query(Component)
            .filter(Component.quantity_on_hand <= Component.minimum_stock * 2)
            .filter(Component.minimum_stock > 0)
            .limit(limit)
            .all()
        )

        predictions = []
        for component in low_stock_components:
            prediction = self.predict_stock_needs(component.id)
            if prediction.get("prediction_status") in ["warning", "critical"]:
                predictions.append({
                    "component_id": component.id,
                    "part_number": component.part_number,
                    "name": component.name,
                    **prediction
                })

        return predictions