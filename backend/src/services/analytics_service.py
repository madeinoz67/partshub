"""
Analytics service for stock analytics and forecasting.

Provides time-series analysis, usage trends, forecasting, dashboard metrics,
and slow-moving stock identification using SQLAlchemy queries on stock_transactions
and component_locations tables.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from ..models import Component, ComponentLocation, StockTransaction, StorageLocation
from ..schemas.analytics import (
    AggregationPeriod,
    ComponentStockSummary,
    DashboardSummaryResponse,
    ForecastDataPoint,
    ForecastHorizon,
    ForecastResponse,
    InventoryHealthMetrics,
    InventorySummaryResponse,
    ReorderSuggestion,
    SlowMovingItem,
    SlowMovingStockResponse,
    StockDataPoint,
    StockDistributionItem,
    StockDistributionResponse,
    StockLevelsResponse,
    StockStatusCategory,
    TopVelocityComponent,
    TopVelocityResponse,
    UsageTrendDataPoint,
    UsageTrendsResponse,
    VelocityMetrics,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Service for stock analytics, forecasting, and inventory metrics.

    Provides methods for:
    - Time-series stock level aggregation
    - Usage trend analysis with velocity metrics
    - Moving average forecasting with reorder suggestions
    - Dashboard summary with inventory KPIs
    - Slow-moving stock identification
    """

    def __init__(self, session: Session):
        """
        Initialize service with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    # ==================== Stock Levels Time-Series ====================

    def get_stock_levels(
        self,
        component_id: str,
        location_id: str | None,
        start_date: datetime,
        end_date: datetime,
        period: AggregationPeriod = AggregationPeriod.DAILY,
    ) -> StockLevelsResponse:
        """
        Get time-series stock level data aggregated by period.

        Calculates running totals of stock quantity over time by analyzing
        stock transactions and aggregating by the requested time period.

        Args:
            component_id: Component UUID to analyze
            location_id: Optional storage location UUID (None = all locations)
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            period: Time aggregation period (daily/weekly/monthly)

        Returns:
            StockLevelsResponse with time-series data and metadata

        Raises:
            HTTPException(404): Component not found
        """
        # Validate component exists
        component = self.session.get(Component, component_id)
        if not component:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404, detail=f"Component {component_id} not found"
            )

        # Get location details if specified
        location = None
        location_name = None
        if location_id:
            location = self.session.get(StorageLocation, location_id)
            if not location:
                from fastapi import HTTPException

                raise HTTPException(
                    status_code=404, detail=f"Location {location_id} not found"
                )
            location_name = location.name

        # Ensure dates are timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=UTC)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=UTC)

        # Get transactions in date range
        query = select(StockTransaction).where(
            and_(
                StockTransaction.component_id == component_id,
                StockTransaction.created_at >= start_date,
                StockTransaction.created_at <= end_date,
            )
        )

        # Filter by location if specified (using to_location_id for add transactions)
        if location_id:
            query = query.where(
                or_(
                    StockTransaction.to_location_id == location_id,
                    StockTransaction.from_location_id == location_id,
                )
            )

        transactions = (
            self.session.execute(query.order_by(StockTransaction.created_at))
            .scalars()
            .all()
        )

        # Aggregate data by period
        data_points = self._aggregate_stock_by_period(
            transactions, start_date, end_date, period, component_id, location_id
        )

        # Get current quantity and reorder threshold
        current_quantity = 0
        reorder_threshold = None

        if location_id:
            comp_loc = (
                self.session.query(ComponentLocation)
                .filter(
                    ComponentLocation.component_id == component_id,
                    ComponentLocation.storage_location_id == location_id,
                )
                .first()
            )
            if comp_loc:
                current_quantity = comp_loc.quantity_on_hand
                reorder_threshold = (
                    comp_loc.reorder_threshold if comp_loc.reorder_enabled else None
                )
        else:
            # Aggregate across all locations
            comp_locs = (
                self.session.query(ComponentLocation)
                .filter(ComponentLocation.component_id == component_id)
                .all()
            )
            current_quantity = sum(cl.quantity_on_hand for cl in comp_locs)
            # Use minimum threshold if any location has reorder enabled
            enabled_thresholds = [
                cl.reorder_threshold for cl in comp_locs if cl.reorder_enabled
            ]
            if enabled_thresholds:
                reorder_threshold = min(enabled_thresholds)

        return StockLevelsResponse(
            component_id=component_id,
            component_name=component.name,
            location_id=location_id,
            location_name=location_name,
            period=period,
            data=data_points,
            metadata={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "current_quantity": current_quantity,
                "reorder_threshold": reorder_threshold,
            },
        )

    def _aggregate_stock_by_period(
        self,
        transactions: list[StockTransaction],
        start_date: datetime,
        end_date: datetime,
        period: AggregationPeriod,
        component_id: str,
        location_id: str | None,
    ) -> list[StockDataPoint]:
        """
        Aggregate stock transactions into time-series data points.

        Args:
            transactions: List of transactions to aggregate
            start_date: Start of date range
            end_date: End of date range
            period: Aggregation period
            component_id: Component UUID
            location_id: Optional location filter

        Returns:
            List of StockDataPoint objects
        """
        # Get initial quantity before start_date
        initial_quantity = self._get_quantity_at_date(
            component_id, location_id, start_date - timedelta(seconds=1)
        )

        # Generate time buckets
        time_buckets = self._generate_time_buckets(start_date, end_date, period)

        # Aggregate transactions into buckets
        data_points = []
        running_quantity = initial_quantity

        for bucket_start, bucket_end in time_buckets:
            # Get transactions in this bucket
            bucket_transactions = [
                t
                for t in transactions
                if bucket_start
                <= (
                    t.created_at.replace(tzinfo=UTC)
                    if t.created_at.tzinfo is None
                    else t.created_at
                )
                < bucket_end
            ]

            # Calculate net change
            net_change = sum(t.quantity_change for t in bucket_transactions)
            running_quantity += net_change

            data_points.append(
                StockDataPoint(
                    timestamp=bucket_start,
                    quantity=max(0, running_quantity),  # Ensure non-negative
                    transaction_count=len(bucket_transactions),
                )
            )

        return data_points

    def _get_quantity_at_date(
        self, component_id: str, location_id: str | None, at_date: datetime
    ) -> int:
        """
        Calculate stock quantity at a specific point in time.

        Args:
            component_id: Component UUID
            location_id: Optional location filter
            at_date: Date to calculate quantity

        Returns:
            Stock quantity at the specified date
        """
        # Ensure date is timezone-aware
        if at_date.tzinfo is None:
            at_date = at_date.replace(tzinfo=UTC)

        # Get all transactions before at_date
        query = select(StockTransaction).where(
            and_(
                StockTransaction.component_id == component_id,
                StockTransaction.created_at <= at_date,
            )
        )

        if location_id:
            query = query.where(
                or_(
                    StockTransaction.to_location_id == location_id,
                    StockTransaction.from_location_id == location_id,
                )
            )

        transactions = self.session.execute(query).scalars().all()

        # Sum quantity changes
        return sum(t.quantity_change for t in transactions)

    def _generate_time_buckets(
        self, start_date: datetime, end_date: datetime, period: AggregationPeriod
    ) -> list[tuple[datetime, datetime]]:
        """
        Generate time bucket boundaries for aggregation.

        Args:
            start_date: Start of date range
            end_date: End of date range
            period: Aggregation period

        Returns:
            List of (bucket_start, bucket_end) tuples
        """
        buckets = []
        current = start_date

        if period == AggregationPeriod.DAILY:
            delta = timedelta(days=1)
        elif period == AggregationPeriod.WEEKLY:
            delta = timedelta(weeks=1)
        elif period == AggregationPeriod.MONTHLY:
            delta = timedelta(days=30)  # Approximate month
        else:
            delta = timedelta(days=1)

        while current < end_date:
            bucket_end = min(current + delta, end_date)
            buckets.append((current, bucket_end))
            current = bucket_end

        return buckets

    # ==================== Usage Trends Analysis ====================

    def get_usage_trends(
        self,
        component_id: str,
        location_id: str | None,
        start_date: datetime,
        end_date: datetime,
        period: AggregationPeriod = AggregationPeriod.DAILY,
    ) -> UsageTrendsResponse:
        """
        Analyze consumption patterns and calculate velocity metrics.

        Args:
            component_id: Component UUID to analyze
            location_id: Optional location UUID (None = all locations)
            start_date: Start of date range
            end_date: End of date range
            period: Time aggregation period

        Returns:
            UsageTrendsResponse with trend data and velocity metrics
        """
        # Validate component exists
        component = self.session.get(Component, component_id)
        if not component:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404, detail=f"Component {component_id} not found"
            )

        # Get location details if specified
        location = None
        location_name = None
        if location_id:
            location = self.session.get(StorageLocation, location_id)
            if location:
                location_name = location.name

        # Ensure dates are timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=UTC)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=UTC)

        # Get transactions in date range
        query = select(StockTransaction).where(
            and_(
                StockTransaction.component_id == component_id,
                StockTransaction.created_at >= start_date,
                StockTransaction.created_at <= end_date,
            )
        )

        if location_id:
            query = query.where(
                or_(
                    StockTransaction.to_location_id == location_id,
                    StockTransaction.from_location_id == location_id,
                )
            )

        transactions = (
            self.session.execute(query.order_by(StockTransaction.created_at))
            .scalars()
            .all()
        )

        # Aggregate usage by period
        trend_data = self._aggregate_usage_by_period(
            transactions, start_date, end_date, period
        )

        # Calculate velocity metrics
        days_analyzed = (end_date - start_date).days or 1
        # Total consumed should be total removed (not net consumed, which can be negative)
        total_consumed = sum(dp.removed for dp in trend_data)

        velocity = VelocityMetrics(
            daily_average=total_consumed / days_analyzed if days_analyzed > 0 else 0.0,
            weekly_average=total_consumed / (days_analyzed / 7)
            if days_analyzed >= 7
            else 0.0,
            monthly_average=total_consumed / (days_analyzed / 30)
            if days_analyzed >= 30
            else 0.0,
            total_consumed=total_consumed,
            days_analyzed=days_analyzed,
        )

        return UsageTrendsResponse(
            component_id=component_id,
            component_name=component.name,
            location_id=location_id,
            location_name=location_name,
            period=period,
            data=trend_data,
            velocity=velocity,
            metadata={
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

    def _aggregate_usage_by_period(
        self,
        transactions: list[StockTransaction],
        start_date: datetime,
        end_date: datetime,
        period: AggregationPeriod,
    ) -> list[UsageTrendDataPoint]:
        """
        Aggregate transactions into usage trend data points.

        Args:
            transactions: List of transactions
            start_date: Start of date range
            end_date: End of date range
            period: Aggregation period

        Returns:
            List of UsageTrendDataPoint objects
        """
        time_buckets = self._generate_time_buckets(start_date, end_date, period)
        data_points = []

        for bucket_start, bucket_end in time_buckets:
            # Get transactions in this bucket
            bucket_transactions = [
                t
                for t in transactions
                if bucket_start
                <= (
                    t.created_at.replace(tzinfo=UTC)
                    if t.created_at.tzinfo is None
                    else t.created_at
                )
                < bucket_end
            ]

            # Calculate added vs removed
            added = sum(
                t.quantity_change for t in bucket_transactions if t.quantity_change > 0
            )
            removed = abs(
                sum(
                    t.quantity_change
                    for t in bucket_transactions
                    if t.quantity_change < 0
                )
            )
            consumed = (
                removed - added
            )  # Net consumption (positive = removed more than added)

            data_points.append(
                UsageTrendDataPoint(
                    timestamp=bucket_start,
                    consumed=consumed,
                    added=added,
                    removed=removed,
                )
            )

        return data_points

    # ==================== Stock Forecasting ====================

    def get_forecast(
        self,
        component_id: str,
        location_id: str | None,
        horizon: ForecastHorizon = ForecastHorizon.TWO_WEEKS,
        lookback_days: int = 30,
    ) -> ForecastResponse:
        """
        Generate moving average forecast with reorder suggestions.

        Uses simple moving average algorithm based on historical consumption
        to predict future stock levels and suggest reorder timing.

        Args:
            component_id: Component UUID to forecast
            location_id: Optional location UUID (None = all locations)
            horizon: Forecast time horizon (7d, 14d, 30d, 90d)
            lookback_days: Historical days to analyze (7-365)

        Returns:
            ForecastResponse with predictions and reorder suggestions
        """
        # Validate component exists
        component = self.session.get(Component, component_id)
        if not component:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=404, detail=f"Component {component_id} not found"
            )

        # Get location details and current quantity
        location_name = None
        current_quantity = 0
        reorder_threshold = None

        if location_id:
            location = self.session.get(StorageLocation, location_id)
            if location:
                location_name = location.name

            comp_loc = (
                self.session.query(ComponentLocation)
                .filter(
                    ComponentLocation.component_id == component_id,
                    ComponentLocation.storage_location_id == location_id,
                )
                .first()
            )
            if comp_loc:
                current_quantity = comp_loc.quantity_on_hand
                reorder_threshold = (
                    comp_loc.reorder_threshold if comp_loc.reorder_enabled else None
                )
        else:
            # Aggregate across all locations
            comp_locs = (
                self.session.query(ComponentLocation)
                .filter(ComponentLocation.component_id == component_id)
                .all()
            )
            current_quantity = sum(cl.quantity_on_hand for cl in comp_locs)
            enabled_thresholds = [
                cl.reorder_threshold for cl in comp_locs if cl.reorder_enabled
            ]
            if enabled_thresholds:
                reorder_threshold = min(enabled_thresholds)

        # Calculate daily velocity from historical data
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=lookback_days)

        query = select(StockTransaction).where(
            and_(
                StockTransaction.component_id == component_id,
                StockTransaction.created_at >= start_date,
                StockTransaction.created_at <= end_date,
            )
        )

        if location_id:
            query = query.where(
                or_(
                    StockTransaction.to_location_id == location_id,
                    StockTransaction.from_location_id == location_id,
                )
            )

        transactions = self.session.execute(query).scalars().all()

        # Calculate daily velocity (negative = consumption)
        total_removed = abs(
            sum(t.quantity_change for t in transactions if t.quantity_change < 0)
        )
        daily_velocity = total_removed / lookback_days if lookback_days > 0 else 0.0

        # Generate forecast data points
        forecast_days = int(horizon.value.rstrip("d"))
        forecast_data = []
        predicted_quantity = current_quantity

        for day in range(1, forecast_days + 1):
            predicted_quantity = max(0, predicted_quantity - daily_velocity)
            forecast_date = end_date + timedelta(days=day)

            # Confidence decreases with horizon distance
            confidence = max(0.5, 1.0 - (day / (forecast_days * 2)))

            will_trigger_reorder = (
                reorder_threshold is not None and predicted_quantity < reorder_threshold
            )

            forecast_data.append(
                ForecastDataPoint(
                    timestamp=forecast_date,
                    predicted_quantity=predicted_quantity,
                    confidence_level=confidence,
                    will_trigger_reorder=will_trigger_reorder,
                )
            )

        # Generate reorder suggestion
        reorder_suggestion = self._generate_reorder_suggestion(
            current_quantity, reorder_threshold, daily_velocity, forecast_data
        )

        return ForecastResponse(
            component_id=component_id,
            component_name=component.name,
            location_id=location_id,
            location_name=location_name,
            current_quantity=current_quantity,
            reorder_threshold=reorder_threshold,
            forecast_horizon=horizon,
            lookback_days=lookback_days,
            data=forecast_data,
            reorder_suggestion=reorder_suggestion,
            metadata={
                "algorithm": "simple_moving_average",
                "daily_velocity": round(daily_velocity, 2),
                "notes": "Confidence decreases with forecast horizon",
            },
        )

    def _generate_reorder_suggestion(
        self,
        current_quantity: int,
        reorder_threshold: int | None,
        daily_velocity: float,
        forecast_data: list[ForecastDataPoint],
    ) -> ReorderSuggestion:
        """
        Generate reorder suggestion based on forecast analysis.

        Args:
            current_quantity: Current stock quantity
            reorder_threshold: Reorder threshold (None if not configured)
            daily_velocity: Daily consumption rate
            forecast_data: List of forecast data points

        Returns:
            ReorderSuggestion with actionable recommendations
        """
        # Check if reorder is needed
        if reorder_threshold is None or daily_velocity <= 0:
            return ReorderSuggestion(
                should_reorder=False,
                suggested_date=None,
                suggested_quantity=None,
                estimated_stockout_date=None,
                days_until_stockout=None,
                confidence_level=0.0,
            )

        # Find when threshold will be breached
        threshold_breach_point = None
        for forecast_point in forecast_data:
            if forecast_point.will_trigger_reorder:
                threshold_breach_point = forecast_point
                break

        if threshold_breach_point is None:
            return ReorderSuggestion(
                should_reorder=False,
                suggested_date=None,
                suggested_quantity=None,
                estimated_stockout_date=None,
                days_until_stockout=None,
                confidence_level=forecast_data[0].confidence_level
                if forecast_data
                else 0.8,
            )

        # Calculate days until stockout
        days_until_stockout = (
            int(current_quantity / daily_velocity) if daily_velocity > 0 else None
        )

        # Estimate stockout date
        estimated_stockout_date = (
            datetime.now(UTC) + timedelta(days=days_until_stockout)
            if days_until_stockout is not None
            else None
        )

        # Suggest reorder date (7 days before threshold breach)
        suggested_date = threshold_breach_point.timestamp - timedelta(days=7)
        if suggested_date < datetime.now(UTC):
            suggested_date = datetime.now(UTC)

        # Suggest quantity (2x threshold to avoid frequent reorders)
        suggested_quantity = reorder_threshold * 2

        return ReorderSuggestion(
            should_reorder=True,
            suggested_date=suggested_date,
            suggested_quantity=suggested_quantity,
            estimated_stockout_date=estimated_stockout_date,
            days_until_stockout=days_until_stockout,
            confidence_level=threshold_breach_point.confidence_level,
        )

    # ==================== Dashboard Summary ====================

    def get_dashboard_summary(
        self, category_id: str | None = None, location_id: str | None = None
    ) -> DashboardSummaryResponse:
        """
        Get aggregated inventory KPIs and top component lists for dashboard.

        Args:
            category_id: Optional category filter
            location_id: Optional location filter

        Returns:
            DashboardSummaryResponse with health metrics and top lists
        """
        # Build base query for component_locations
        query = select(ComponentLocation).options(
            joinedload(ComponentLocation.component),
            joinedload(ComponentLocation.storage_location),
        )

        # Apply filters
        if location_id:
            query = query.where(ComponentLocation.storage_location_id == location_id)

        if category_id:
            query = query.join(Component).where(Component.category_id == category_id)

        comp_locs = self.session.execute(query).scalars().all()

        # Calculate health metrics
        total_components = len(set(cl.component_id for cl in comp_locs))
        low_stock_count = sum(1 for cl in comp_locs if cl.needs_reorder)
        out_of_stock_count = sum(1 for cl in comp_locs if cl.quantity_on_hand == 0)

        # Calculate total inventory value
        total_value = 0.0
        for cl in comp_locs:
            if cl.component.average_purchase_price:
                total_value += cl.quantity_on_hand * float(
                    cl.component.average_purchase_price
                )

        # Calculate average velocity
        velocities = []
        for cl in comp_locs:
            velocity = self._calculate_component_velocity(cl.component_id, days=30)
            velocities.append(velocity)

        avg_velocity = sum(velocities) / len(velocities) if velocities else 0.0

        health_metrics = InventoryHealthMetrics(
            total_components=total_components,
            low_stock_count=low_stock_count,
            out_of_stock_count=out_of_stock_count,
            total_inventory_value=total_value,
            active_alerts_count=low_stock_count,  # Same as low_stock_count
            average_stock_velocity=avg_velocity,
        )

        # Get top low stock components (by shortage urgency)
        top_low_stock = self._get_top_low_stock(comp_locs, limit=10)

        # Get top consumers (by velocity)
        top_consumers = self._get_top_consumers(comp_locs, limit=10)

        # Count recent activity (last 7 days)
        week_ago = datetime.now(UTC) - timedelta(days=7)
        recent_count = (
            self.session.query(func.count(StockTransaction.id))
            .filter(StockTransaction.created_at >= week_ago)
            .scalar()
        ) or 0

        return DashboardSummaryResponse(
            health_metrics=health_metrics,
            top_low_stock=top_low_stock,
            top_consumers=top_consumers,
            recent_activity_count=recent_count,
            metadata={
                "last_updated": datetime.now(UTC).isoformat(),
                "category_filter": category_id,
                "location_filter": location_id,
            },
        )

    def _calculate_component_velocity(self, component_id: str, days: int = 30) -> float:
        """
        Calculate daily consumption velocity for a component.

        Args:
            component_id: Component UUID
            days: Number of days to analyze

        Returns:
            Daily consumption rate (units/day)
        """
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        transactions = (
            self.session.query(StockTransaction)
            .filter(
                and_(
                    StockTransaction.component_id == component_id,
                    StockTransaction.created_at >= start_date,
                    StockTransaction.created_at <= end_date,
                )
            )
            .all()
        )

        total_removed = abs(
            sum(t.quantity_change for t in transactions if t.quantity_change < 0)
        )
        return total_removed / days if days > 0 else 0.0

    def _get_top_low_stock(
        self, comp_locs: list[ComponentLocation], limit: int = 10
    ) -> list[ComponentStockSummary]:
        """
        Get top components by shortage urgency.

        Args:
            comp_locs: List of component locations
            limit: Max items to return

        Returns:
            List of ComponentStockSummary objects
        """
        # Filter to components that need reorder
        low_stock = [cl for cl in comp_locs if cl.needs_reorder]

        # Calculate days until stockout for each
        urgency_list = []
        for cl in low_stock:
            velocity = self._calculate_component_velocity(cl.component_id, days=30)
            days_until_stockout = (
                int(cl.quantity_on_hand / velocity) if velocity > 0 else None
            )

            urgency_list.append((cl, days_until_stockout))

        # Sort by urgency (lowest days_until_stockout first, None values last)
        urgency_list.sort(
            key=lambda x: (x[1] is None, x[1] if x[1] is not None else float("inf"))
        )

        # Build summaries
        summaries = []
        seen_components = set()

        for cl, days_until_stockout in urgency_list[:limit]:
            if cl.component_id in seen_components:
                continue
            seen_components.add(cl.component_id)

            # Get total quantity across all locations
            total_qty = sum(
                loc.quantity_on_hand
                for loc in comp_locs
                if loc.component_id == cl.component_id
            )

            # Count locations
            location_count = sum(
                1 for loc in comp_locs if loc.component_id == cl.component_id
            )

            velocity = self._calculate_component_velocity(cl.component_id, days=30)

            summaries.append(
                ComponentStockSummary(
                    component_id=cl.component_id,
                    component_name=cl.component.name,
                    total_quantity=total_qty,
                    locations_count=location_count,
                    has_active_alerts=True,
                    daily_velocity=velocity,
                    days_until_stockout=days_until_stockout,
                )
            )

        return summaries

    def _get_top_consumers(
        self, comp_locs: list[ComponentLocation], limit: int = 10
    ) -> list[ComponentStockSummary]:
        """
        Get top components by consumption velocity.

        Args:
            comp_locs: List of component locations
            limit: Max items to return

        Returns:
            List of ComponentStockSummary objects
        """
        # Calculate velocity for each unique component
        velocity_list = []
        seen_components = set()

        for cl in comp_locs:
            if cl.component_id in seen_components:
                continue
            seen_components.add(cl.component_id)

            velocity = self._calculate_component_velocity(cl.component_id, days=30)
            if velocity > 0:  # Only include components with consumption
                velocity_list.append((cl, velocity))

        # Sort by velocity (highest first)
        velocity_list.sort(key=lambda x: x[1], reverse=True)

        # Build summaries
        summaries = []
        for cl, velocity in velocity_list[:limit]:
            # Get total quantity across all locations
            total_qty = sum(
                loc.quantity_on_hand
                for loc in comp_locs
                if loc.component_id == cl.component_id
            )

            # Count locations
            location_count = sum(
                1 for loc in comp_locs if loc.component_id == cl.component_id
            )

            # Check if has active alerts
            has_alerts = any(
                loc.needs_reorder
                for loc in comp_locs
                if loc.component_id == cl.component_id
            )

            # Calculate days until stockout
            days_until_stockout = int(total_qty / velocity) if velocity > 0 else None

            summaries.append(
                ComponentStockSummary(
                    component_id=cl.component_id,
                    component_name=cl.component.name,
                    total_quantity=total_qty,
                    locations_count=location_count,
                    has_active_alerts=has_alerts,
                    daily_velocity=velocity,
                    days_until_stockout=days_until_stockout,
                )
            )

        return summaries

    # ==================== Slow-Moving Stock Analysis ====================

    def get_slow_moving_stock(
        self,
        min_days_of_stock: int = 180,
        min_days_since_last_use: int | None = None,
    ) -> SlowMovingStockResponse:
        """
        Identify components with low consumption velocity (slow-moving/obsolete).

        Args:
            min_days_of_stock: Minimum days of stock to classify as slow-moving
            min_days_since_last_use: Optional minimum days since last use filter

        Returns:
            SlowMovingStockResponse with slow-moving items and metrics
        """
        # Get all component locations
        comp_locs = (
            self.session.query(ComponentLocation)
            .options(
                joinedload(ComponentLocation.component),
            )
            .all()
        )

        slow_moving_items = []
        total_value_locked = 0.0

        for cl in comp_locs:
            if cl.quantity_on_hand == 0:
                continue  # Skip out-of-stock items

            # Calculate velocity
            velocity = self._calculate_component_velocity(cl.component_id, days=90)

            # Calculate days of stock
            days_of_stock = (
                cl.quantity_on_hand / velocity if velocity > 0 else float("inf")
            )

            # Check if meets slow-moving criteria
            if days_of_stock < min_days_of_stock:
                continue

            # Get last used date
            last_used_date, days_since_last_use = self._get_last_used_info(
                cl.component_id
            )

            # Apply days_since_last_use filter if specified
            if min_days_since_last_use is not None:
                if (
                    days_since_last_use is None
                    or days_since_last_use < min_days_since_last_use
                ):
                    continue

            # Calculate inventory value
            inventory_value = 0.0
            if cl.component.average_purchase_price:
                inventory_value = cl.quantity_on_hand * float(
                    cl.component.average_purchase_price
                )

            total_value_locked += inventory_value

            slow_moving_items.append(
                SlowMovingItem(
                    component_id=cl.component_id,
                    component_name=cl.component.name,
                    total_quantity=cl.quantity_on_hand,
                    daily_velocity=velocity,
                    days_of_stock=days_of_stock
                    if days_of_stock != float("inf")
                    else 9999.0,
                    last_used_date=last_used_date,
                    days_since_last_use=days_since_last_use,
                    inventory_value=inventory_value,
                )
            )

        # Sort by days_of_stock (descending)
        slow_moving_items.sort(key=lambda x: x.days_of_stock, reverse=True)

        return SlowMovingStockResponse(
            items=slow_moving_items,
            total_count=len(slow_moving_items),
            total_value_locked=total_value_locked,
            metadata={
                "min_days_of_stock": min_days_of_stock,
                "min_days_since_last_use": min_days_since_last_use,
                "analysis_date": datetime.now(UTC).isoformat(),
            },
        )

    def _get_last_used_info(
        self, component_id: str
    ) -> tuple[datetime | None, int | None]:
        """
        Get last used date and days since last use for a component.

        Args:
            component_id: Component UUID

        Returns:
            Tuple of (last_used_date, days_since_last_use)
        """
        # Get last remove transaction
        last_remove = (
            self.session.query(StockTransaction)
            .filter(
                StockTransaction.component_id == component_id,
                StockTransaction.quantity_change < 0,
            )
            .order_by(desc(StockTransaction.created_at))
            .first()
        )

        if not last_remove:
            return None, None

        last_used_date = last_remove.created_at
        # Ensure last_used_date is timezone-aware
        if last_used_date.tzinfo is None:
            last_used_date = last_used_date.replace(tzinfo=UTC)

        days_since_last_use = (datetime.now(UTC) - last_used_date).days

        return last_used_date, days_since_last_use

    # ==================== Inventory-Wide Analytics ====================

    def get_inventory_summary(self) -> InventorySummaryResponse:
        """
        Get aggregate inventory KPIs across all components.

        Calculates summary statistics including total value, stock levels,
        and health indicators for the entire inventory.

        Returns:
            InventorySummaryResponse with aggregate KPIs
        """
        # Get all component locations
        comp_locs = (
            self.session.query(ComponentLocation)
            .options(
                joinedload(ComponentLocation.component),
                joinedload(ComponentLocation.storage_location),
            )
            .all()
        )

        # Calculate metrics
        unique_components = set()
        total_stock_value = 0.0
        low_stock_count = 0
        out_of_stock_count = 0
        overstocked_count = 0
        stock_level_percentages = []
        unique_locations = set()

        components_with_threshold = 0
        components_without_threshold = 0

        for cl in comp_locs:
            unique_components.add(cl.component_id)
            unique_locations.add(cl.storage_location_id)

            # Calculate stock value
            if cl.component.average_purchase_price:
                total_stock_value += cl.quantity_on_hand * float(
                    cl.component.average_purchase_price
                )

            # Check stock status
            if cl.quantity_on_hand == 0:
                out_of_stock_count += 1

            # Check reorder status
            if cl.reorder_enabled and cl.reorder_threshold:
                components_with_threshold += 1

                if cl.needs_reorder:
                    low_stock_count += 1

                # Check for overstocked (>= 1.5x threshold)
                if cl.quantity_on_hand >= (cl.reorder_threshold * 1.5):
                    overstocked_count += 1

                # Calculate stock level percentage
                percentage = (cl.quantity_on_hand / cl.reorder_threshold) * 100
                stock_level_percentages.append(percentage)
            else:
                components_without_threshold += 1

        # Calculate average stock level percentage
        avg_stock_level_pct = (
            sum(stock_level_percentages) / len(stock_level_percentages)
            if stock_level_percentages
            else 0.0
        )

        return InventorySummaryResponse(
            total_components=len(unique_components),
            total_stock_value=total_stock_value,
            low_stock_count=low_stock_count,
            out_of_stock_count=out_of_stock_count,
            overstocked_count=overstocked_count,
            average_stock_level_percentage=avg_stock_level_pct,
            total_locations=len(unique_locations),
            metadata={
                "timestamp": datetime.now(UTC).isoformat(),
                "components_with_threshold": components_with_threshold,
                "components_without_threshold": components_without_threshold,
            },
        )

    def get_stock_distribution(self) -> StockDistributionResponse:
        """
        Get breakdown of components by stock status.

        Categorizes each component into critical/low/ok/overstocked based
        on current quantity vs reorder threshold.

        Returns:
            StockDistributionResponse with distribution breakdown
        """
        # Get all component locations
        comp_locs = (
            self.session.query(ComponentLocation)
            .options(joinedload(ComponentLocation.component))
            .all()
        )

        # Categorize components by unique component_id
        component_status_map = {}

        for cl in comp_locs:
            # Skip if already categorized (use worst status per component)
            if cl.component_id in component_status_map:
                current_status = component_status_map[cl.component_id]
                # Priority: CRITICAL > LOW > OK > OVERSTOCKED
                priority = {
                    StockStatusCategory.CRITICAL: 0,
                    StockStatusCategory.LOW: 1,
                    StockStatusCategory.OK: 2,
                    StockStatusCategory.OVERSTOCKED: 3,
                }
                # Only update if new status is higher priority (lower number)
                new_status = self._categorize_stock_status(cl)
                if priority[new_status] < priority[current_status]:
                    component_status_map[cl.component_id] = new_status
            else:
                component_status_map[cl.component_id] = self._categorize_stock_status(
                    cl
                )

        # Count by status
        status_counts = {
            StockStatusCategory.CRITICAL: 0,
            StockStatusCategory.LOW: 0,
            StockStatusCategory.OK: 0,
            StockStatusCategory.OVERSTOCKED: 0,
        }

        for status in component_status_map.values():
            status_counts[status] += 1

        total_components = len(component_status_map)

        # Build distribution items
        distribution = []
        for status, count in status_counts.items():
            percentage = (
                (count / total_components * 100) if total_components > 0 else 0.0
            )
            distribution.append(
                StockDistributionItem(
                    status=status,
                    count=count,
                    percentage=round(percentage, 2),
                )
            )

        return StockDistributionResponse(
            total_components=total_components,
            distribution=distribution,
            timestamp=datetime.now(UTC),
        )

    def _categorize_stock_status(
        self, component_location: ComponentLocation
    ) -> StockStatusCategory:
        """
        Categorize a component location by stock status.

        Args:
            component_location: ComponentLocation to categorize

        Returns:
            StockStatusCategory enum value
        """
        qty = component_location.quantity_on_hand

        # Critical: qty = 0
        if qty == 0:
            return StockStatusCategory.CRITICAL

        # If no threshold configured, assume OK
        if (
            not component_location.reorder_enabled
            or not component_location.reorder_threshold
        ):
            return StockStatusCategory.OK

        threshold = component_location.reorder_threshold

        # Low: qty > 0 and qty <= threshold
        if qty <= threshold:
            return StockStatusCategory.LOW

        # Overstocked: qty >= threshold * 1.5
        if qty >= (threshold * 1.5):
            return StockStatusCategory.OVERSTOCKED

        # OK: qty > threshold and qty < threshold * 1.5
        return StockStatusCategory.OK

    def get_top_velocity(
        self,
        limit: int = 10,
        lookback_days: int = 30,
        min_transactions: int = 2,
    ) -> TopVelocityResponse:
        """
        Get top N fastest-moving components by consumption velocity.

        Analyzes consumption patterns across all components and returns
        the fastest movers with stockout predictions.

        Args:
            limit: Maximum number of components to return (1-50)
            lookback_days: Number of days to analyze for velocity (7-365)
            min_transactions: Minimum transactions required to be included (1+)

        Returns:
            TopVelocityResponse with top velocity components
        """
        # Get all component locations
        comp_locs = (
            self.session.query(ComponentLocation)
            .options(
                joinedload(ComponentLocation.component),
                joinedload(ComponentLocation.storage_location),
            )
            .all()
        )

        # Calculate velocity for each unique component
        velocity_data = []
        seen_components = set()

        for cl in comp_locs:
            if cl.component_id in seen_components:
                continue
            seen_components.add(cl.component_id)

            # Get velocity and transaction count
            velocity, transaction_count = self._calculate_component_velocity_with_count(
                cl.component_id, days=lookback_days
            )

            # Skip if insufficient transactions
            if transaction_count < min_transactions:
                continue

            # Skip if zero velocity
            if velocity <= 0:
                continue

            # Calculate total quantity across all locations for this component
            total_qty = sum(
                loc.quantity_on_hand
                for loc in comp_locs
                if loc.component_id == cl.component_id
            )

            # Calculate days until stockout
            days_until_stockout = int(total_qty / velocity) if velocity > 0 else None

            # Get primary location (highest quantity)
            primary_loc = max(
                (loc for loc in comp_locs if loc.component_id == cl.component_id),
                key=lambda x: x.quantity_on_hand,
            )

            velocity_data.append(
                {
                    "component_id": cl.component_id,
                    "component_name": cl.component.name,
                    "part_number": cl.component.part_number,
                    "daily_velocity": velocity,
                    "weekly_velocity": velocity * 7,
                    "monthly_velocity": velocity * 30,
                    "current_quantity": total_qty,
                    "days_until_stockout": days_until_stockout,
                    "location_name": primary_loc.storage_location.name
                    if primary_loc.storage_location
                    else None,
                }
            )

        # Sort by daily velocity (highest first)
        velocity_data.sort(key=lambda x: x["daily_velocity"], reverse=True)

        # Take top N
        top_components = velocity_data[:limit]

        # Build response
        components = [TopVelocityComponent(**comp) for comp in top_components]

        return TopVelocityResponse(
            components=components,
            period_analyzed=f"last_{lookback_days}_days",
            total_components_analyzed=len(seen_components),
            metadata={
                "lookback_days": lookback_days,
                "min_transactions": min_transactions,
                "limit": limit,
            },
        )

    def _calculate_component_velocity_with_count(
        self, component_id: str, days: int = 30
    ) -> tuple[float, int]:
        """
        Calculate daily consumption velocity and transaction count for a component.

        Args:
            component_id: Component UUID
            days: Number of days to analyze

        Returns:
            Tuple of (daily_velocity, transaction_count)
        """
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=days)

        transactions = (
            self.session.query(StockTransaction)
            .filter(
                and_(
                    StockTransaction.component_id == component_id,
                    StockTransaction.created_at >= start_date,
                    StockTransaction.created_at <= end_date,
                    StockTransaction.quantity_change < 0,  # Only removals
                )
            )
            .all()
        )

        total_removed = abs(sum(t.quantity_change for t in transactions))
        transaction_count = len(transactions)
        velocity = total_removed / days if days > 0 else 0.0

        return velocity, transaction_count
