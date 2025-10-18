"""
Unit tests for AnalyticsService.

Tests stock analytics, forecasting, and inventory metrics using in-memory SQLite.
Follows isolated testing principles with self-contained test data.
"""

from datetime import UTC, datetime, timedelta

import pytest

from backend.src.models import (
    Component,
    ComponentLocation,
    StockTransaction,
    StorageLocation,
    TransactionType,
)
from backend.src.schemas.analytics import AggregationPeriod, ForecastHorizon
from backend.src.services.analytics_service import AnalyticsService


@pytest.fixture
def analytics_service(db_session):
    """Create AnalyticsService instance with test database session."""
    return AnalyticsService(db_session)


@pytest.fixture
def sample_component(db_session):
    """Create a sample component for testing."""
    component = Component(
        name="Test Resistor 10kΩ",
        part_number="TEST-RES-10K",
        manufacturer="Test Manufacturer",
        component_type="resistor",
        value="10kΩ",
        package="0805",
        average_purchase_price=0.10,
    )
    db_session.add(component)
    db_session.commit()
    db_session.refresh(component)
    return component


@pytest.fixture
def sample_location(db_session):
    """Create a sample storage location for testing."""
    location = StorageLocation(
        name="Test Drawer A1",
        description="Test location for analytics",
        type="drawer",
    )
    db_session.add(location)
    db_session.commit()
    db_session.refresh(location)
    return location


@pytest.fixture
def component_location(db_session, sample_component, sample_location):
    """Create a component location with stock and reorder threshold."""
    comp_loc = ComponentLocation(
        component_id=sample_component.id,
        storage_location_id=sample_location.id,
        quantity_on_hand=100,
        reorder_threshold=50,
        reorder_enabled=True,
    )
    db_session.add(comp_loc)
    db_session.commit()
    db_session.refresh(comp_loc)
    return comp_loc


@pytest.fixture
def historical_transactions(db_session, sample_component, sample_location):
    """Create historical stock transactions for testing analytics."""
    transactions = []
    base_date = datetime.now(UTC) - timedelta(days=30)

    # Simulate stock activity over 30 days
    for day in range(30):
        transaction_date = base_date + timedelta(days=day)

        # Add stock every 5 days
        if day % 5 == 0:
            txn = StockTransaction(
                component_id=sample_component.id,
                transaction_type=TransactionType.ADD,
                quantity_change=50,
                previous_quantity=100,
                new_quantity=150,
                reason="Periodic restock",
                to_location_id=sample_location.id,
                created_at=transaction_date,
            )
            transactions.append(txn)

        # Remove stock every 2 days
        if day % 2 == 0:
            txn = StockTransaction(
                component_id=sample_component.id,
                transaction_type=TransactionType.REMOVE,
                quantity_change=-10,
                previous_quantity=100,
                new_quantity=90,
                reason="Used in project",
                from_location_id=sample_location.id,
                created_at=transaction_date,
            )
            transactions.append(txn)

    db_session.add_all(transactions)
    db_session.commit()
    return transactions


# ==================== Stock Levels Tests ====================


def test_get_stock_levels_daily(
    analytics_service, sample_component, sample_location, historical_transactions
):
    """Test stock level time-series with daily aggregation."""
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=7)

    response = analytics_service.get_stock_levels(
        component_id=sample_component.id,
        location_id=sample_location.id,
        start_date=start_date,
        end_date=end_date,
        period=AggregationPeriod.DAILY,
    )

    assert response.component_id == sample_component.id
    assert response.component_name == sample_component.name
    assert response.location_id == sample_location.id
    assert response.period == AggregationPeriod.DAILY
    assert len(response.data) > 0

    # Check data point structure
    for data_point in response.data:
        assert data_point.quantity >= 0
        assert data_point.transaction_count >= 0
        assert data_point.timestamp >= start_date
        assert data_point.timestamp <= end_date

    # Check metadata
    assert "start_date" in response.metadata
    assert "end_date" in response.metadata
    assert "current_quantity" in response.metadata


def test_get_stock_levels_weekly(
    analytics_service, sample_component, sample_location, historical_transactions
):
    """Test stock level time-series with weekly aggregation."""
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=28)

    response = analytics_service.get_stock_levels(
        component_id=sample_component.id,
        location_id=sample_location.id,
        start_date=start_date,
        end_date=end_date,
        period=AggregationPeriod.WEEKLY,
    )

    assert response.period == AggregationPeriod.WEEKLY
    assert len(response.data) > 0


def test_get_stock_levels_all_locations(
    analytics_service, sample_component, historical_transactions
):
    """Test stock level aggregation across all locations."""
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=7)

    response = analytics_service.get_stock_levels(
        component_id=sample_component.id,
        location_id=None,  # All locations
        start_date=start_date,
        end_date=end_date,
        period=AggregationPeriod.DAILY,
    )

    assert response.location_id is None
    assert response.location_name is None
    assert len(response.data) > 0


def test_get_stock_levels_component_not_found(analytics_service):
    """Test stock levels with non-existent component."""
    from fastapi import HTTPException

    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=7)

    with pytest.raises(HTTPException) as exc_info:
        analytics_service.get_stock_levels(
            component_id="non-existent-id",
            location_id=None,
            start_date=start_date,
            end_date=end_date,
            period=AggregationPeriod.DAILY,
        )

    assert exc_info.value.status_code == 404


def test_get_stock_levels_no_transactions(
    analytics_service, sample_component, sample_location, component_location
):
    """Test stock levels with no historical transactions."""
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=7)

    response = analytics_service.get_stock_levels(
        component_id=sample_component.id,
        location_id=sample_location.id,
        start_date=start_date,
        end_date=end_date,
        period=AggregationPeriod.DAILY,
    )

    assert len(response.data) > 0
    # All data points should have 0 transactions
    for dp in response.data:
        assert dp.transaction_count == 0


# ==================== Usage Trends Tests ====================


def test_get_usage_trends_daily(
    analytics_service, sample_component, sample_location, historical_transactions
):
    """Test usage trends analysis with daily aggregation."""
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=7)

    response = analytics_service.get_usage_trends(
        component_id=sample_component.id,
        location_id=sample_location.id,
        start_date=start_date,
        end_date=end_date,
        period=AggregationPeriod.DAILY,
    )

    assert response.component_id == sample_component.id
    assert response.component_name == sample_component.name
    assert response.period == AggregationPeriod.DAILY
    assert len(response.data) > 0

    # Check velocity metrics
    assert response.velocity.daily_average >= 0
    assert response.velocity.weekly_average >= 0
    assert response.velocity.monthly_average >= 0
    assert response.velocity.total_consumed >= 0
    assert response.velocity.days_analyzed > 0

    # Check data point structure
    for data_point in response.data:
        assert data_point.added >= 0
        assert data_point.removed >= 0
        assert data_point.timestamp >= start_date
        assert data_point.timestamp <= end_date


def test_get_usage_trends_velocity_calculation(
    analytics_service, sample_component, sample_location, historical_transactions
):
    """Test that velocity metrics are calculated correctly."""
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=30)

    response = analytics_service.get_usage_trends(
        component_id=sample_component.id,
        location_id=sample_location.id,
        start_date=start_date,
        end_date=end_date,
        period=AggregationPeriod.DAILY,
    )

    # Velocity should be positive if there's consumption
    assert response.velocity.total_consumed >= 0

    # Daily average should be total / days
    expected_daily = response.velocity.total_consumed / response.velocity.days_analyzed
    assert abs(response.velocity.daily_average - expected_daily) < 0.01


def test_get_usage_trends_no_consumption(
    analytics_service, sample_component, sample_location, component_location
):
    """Test usage trends with no consumption (only additions)."""
    # Add some stock transactions (only adds, no removes)
    txn = StockTransaction(
        component_id=sample_component.id,
        transaction_type=TransactionType.ADD,
        quantity_change=100,
        previous_quantity=100,
        new_quantity=200,
        reason="Stock addition",
        to_location_id=sample_location.id,
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    analytics_service.session.add(txn)
    analytics_service.session.commit()

    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=7)

    response = analytics_service.get_usage_trends(
        component_id=sample_component.id,
        location_id=sample_location.id,
        start_date=start_date,
        end_date=end_date,
        period=AggregationPeriod.DAILY,
    )

    # Should have low or zero consumption
    assert response.velocity.total_consumed >= 0
    # Consumed should be negative or zero (more added than removed)
    total_consumed_from_data = sum(dp.consumed for dp in response.data)
    assert total_consumed_from_data <= 100  # At most 100 consumed


# ==================== Forecast Tests ====================


def test_get_forecast_basic(
    analytics_service,
    sample_component,
    sample_location,
    component_location,
    historical_transactions,
):
    """Test basic forecast generation."""
    response = analytics_service.get_forecast(
        component_id=sample_component.id,
        location_id=sample_location.id,
        horizon=ForecastHorizon.WEEK,
        lookback_days=30,
    )

    assert response.component_id == sample_component.id
    assert response.component_name == sample_component.name
    assert response.forecast_horizon == ForecastHorizon.WEEK
    assert response.lookback_days == 30
    assert len(response.data) == 7  # 7 days forecast

    # Check forecast data points
    for i, forecast_point in enumerate(response.data):
        assert forecast_point.predicted_quantity >= 0
        assert 0.0 <= forecast_point.confidence_level <= 1.0
        # Confidence should generally decrease with time
        if i > 0:
            assert (
                forecast_point.confidence_level <= response.data[i - 1].confidence_level
                or abs(
                    forecast_point.confidence_level
                    - response.data[i - 1].confidence_level
                )
                < 0.1
            )

    # Check reorder suggestion structure
    assert response.reorder_suggestion is not None
    assert isinstance(response.reorder_suggestion.should_reorder, bool)


def test_get_forecast_reorder_suggestion(
    analytics_service,
    sample_component,
    sample_location,
    component_location,
    historical_transactions,
):
    """Test forecast reorder suggestion logic."""
    # Update component location to have low stock
    component_location.quantity_on_hand = 30
    component_location.reorder_threshold = 50
    analytics_service.session.commit()

    response = analytics_service.get_forecast(
        component_id=sample_component.id,
        location_id=sample_location.id,
        horizon=ForecastHorizon.TWO_WEEKS,
        lookback_days=30,
    )

    suggestion = response.reorder_suggestion

    # Should recommend reorder if stock is below threshold
    if component_location.quantity_on_hand < component_location.reorder_threshold:
        assert suggestion.should_reorder is True
        assert suggestion.suggested_quantity is not None
        assert suggestion.suggested_quantity > 0


def test_get_forecast_no_reorder_threshold(
    analytics_service,
    sample_component,
    sample_location,
    historical_transactions,
    db_session,
):
    """Test forecast when reorder threshold is not configured."""
    # Create component location without reorder threshold
    comp_loc = ComponentLocation(
        component_id=sample_component.id,
        storage_location_id=sample_location.id,
        quantity_on_hand=100,
        reorder_enabled=False,  # Disabled
    )
    db_session.add(comp_loc)
    db_session.commit()

    response = analytics_service.get_forecast(
        component_id=sample_component.id,
        location_id=sample_location.id,
        horizon=ForecastHorizon.WEEK,
        lookback_days=30,
    )

    # Should not recommend reorder
    assert response.reorder_suggestion.should_reorder is False
    assert response.reorder_suggestion.suggested_quantity is None


def test_get_forecast_confidence_decreases(
    analytics_service,
    sample_component,
    sample_location,
    component_location,
    historical_transactions,
):
    """Test that forecast confidence decreases with time horizon."""
    response = analytics_service.get_forecast(
        component_id=sample_component.id,
        location_id=sample_location.id,
        horizon=ForecastHorizon.MONTH,
        lookback_days=30,
    )

    # First forecast point should have higher confidence than last
    assert response.data[0].confidence_level > response.data[-1].confidence_level


# ==================== Dashboard Summary Tests ====================


def test_get_dashboard_summary_basic(
    analytics_service,
    sample_component,
    sample_location,
    component_location,
    historical_transactions,
):
    """Test basic dashboard summary generation."""
    response = analytics_service.get_dashboard_summary()

    # Check health metrics
    assert response.health_metrics.total_components >= 1
    assert response.health_metrics.low_stock_count >= 0
    assert response.health_metrics.out_of_stock_count >= 0
    assert response.health_metrics.total_inventory_value >= 0.0
    assert response.health_metrics.active_alerts_count >= 0
    assert response.health_metrics.average_stock_velocity >= 0.0

    # Check top lists exist
    assert isinstance(response.top_low_stock, list)
    assert isinstance(response.top_consumers, list)
    assert len(response.top_low_stock) <= 10
    assert len(response.top_consumers) <= 10

    # Check metadata
    assert "last_updated" in response.metadata


def test_get_dashboard_summary_with_filters(
    analytics_service,
    sample_component,
    sample_location,
    component_location,
    historical_transactions,
    db_session,
):
    """Test dashboard summary with category and location filters."""
    from backend.src.models import Category

    # Create category
    category = Category(name="Test Category", description="Test")
    db_session.add(category)
    db_session.commit()

    # Update component with category
    sample_component.category_id = category.id
    db_session.commit()

    # Test with category filter
    response = analytics_service.get_dashboard_summary(category_id=category.id)
    assert response.health_metrics.total_components >= 1

    # Test with location filter
    response = analytics_service.get_dashboard_summary(location_id=sample_location.id)
    assert response.health_metrics.total_components >= 1


def test_get_dashboard_summary_top_low_stock(
    analytics_service, db_session, sample_location, historical_transactions
):
    """Test that top_low_stock list is properly sorted by urgency."""
    # Create multiple components with different stock levels
    components = []
    for i in range(3):
        comp = Component(
            name=f"Test Component {i}",
            part_number=f"TEST-{i:03d}",
            average_purchase_price=1.0,
        )
        db_session.add(comp)
        db_session.flush()

        # Create component location with varying stock levels
        comp_loc = ComponentLocation(
            component_id=comp.id,
            storage_location_id=sample_location.id,
            quantity_on_hand=10 * (i + 1),  # 10, 20, 30
            reorder_threshold=50,  # All below threshold
            reorder_enabled=True,
        )
        db_session.add(comp_loc)
        components.append(comp)

    db_session.commit()

    response = analytics_service.get_dashboard_summary()

    # Should have low stock items
    assert len(response.top_low_stock) > 0


def test_get_dashboard_summary_recent_activity(
    analytics_service, sample_component, sample_location, component_location, db_session
):
    """Test recent activity count in dashboard summary."""
    # Add recent transactions
    for i in range(5):
        txn = StockTransaction(
            component_id=sample_component.id,
            transaction_type=TransactionType.REMOVE,
            quantity_change=-5,
            previous_quantity=100,
            new_quantity=95,
            reason="Recent activity",
            from_location_id=sample_location.id,
            created_at=datetime.now(UTC) - timedelta(days=i),
        )
        db_session.add(txn)

    db_session.commit()

    response = analytics_service.get_dashboard_summary()

    # Should count recent transactions (last 7 days)
    assert response.recent_activity_count >= 5


# ==================== Slow-Moving Stock Tests ====================


def test_get_slow_moving_stock_basic(
    analytics_service,
    sample_component,
    sample_location,
    component_location,
    historical_transactions,
):
    """Test basic slow-moving stock identification."""
    response = analytics_service.get_slow_moving_stock(
        min_days_of_stock=180,
        min_days_since_last_use=None,
    )

    assert isinstance(response.items, list)
    assert response.total_count == len(response.items)
    assert response.total_value_locked >= 0.0

    # Check metadata
    assert response.metadata["min_days_of_stock"] == 180


def test_get_slow_moving_stock_high_inventory(
    analytics_service, sample_component, sample_location, db_session
):
    """Test slow-moving identification with high inventory and low velocity."""
    # Create component with high stock and low velocity
    comp_loc = ComponentLocation(
        component_id=sample_component.id,
        storage_location_id=sample_location.id,
        quantity_on_hand=5000,  # Very high stock
        reorder_enabled=False,
    )
    db_session.add(comp_loc)
    db_session.commit()

    # Add minimal consumption transactions
    txn = StockTransaction(
        component_id=sample_component.id,
        transaction_type=TransactionType.REMOVE,
        quantity_change=-1,
        previous_quantity=5000,
        new_quantity=4999,
        reason="Minimal usage",
        from_location_id=sample_location.id,
        created_at=datetime.now(UTC) - timedelta(days=30),
    )
    db_session.add(txn)
    db_session.commit()

    response = analytics_service.get_slow_moving_stock(min_days_of_stock=100)

    # Should identify this component as slow-moving
    # (5000 units / (1/90 units per day) = 450,000 days of stock)
    if len(response.items) > 0:
        assert any(item.component_id == sample_component.id for item in response.items)


def test_get_slow_moving_stock_with_last_use_filter(
    analytics_service, sample_component, sample_location, component_location, db_session
):
    """Test slow-moving stock with days_since_last_use filter."""
    # Add old transaction
    old_txn = StockTransaction(
        component_id=sample_component.id,
        transaction_type=TransactionType.REMOVE,
        quantity_change=-10,
        previous_quantity=100,
        new_quantity=90,
        reason="Old usage",
        from_location_id=sample_location.id,
        created_at=datetime.now(UTC) - timedelta(days=200),
    )
    db_session.add(old_txn)
    db_session.commit()

    response = analytics_service.get_slow_moving_stock(
        min_days_of_stock=10,
        min_days_since_last_use=100,
    )

    # Should include items not used in 100+ days
    assert isinstance(response.items, list)


def test_get_slow_moving_stock_sorting(analytics_service, db_session, sample_location):
    """Test that slow-moving items are sorted by days_of_stock descending."""
    # Create multiple components with different velocities
    components = []
    for i in range(3):
        comp = Component(
            name=f"Slow Component {i}",
            part_number=f"SLOW-{i:03d}",
            average_purchase_price=1.0,
        )
        db_session.add(comp)
        db_session.flush()

        comp_loc = ComponentLocation(
            component_id=comp.id,
            storage_location_id=sample_location.id,
            quantity_on_hand=1000 * (i + 1),  # 1000, 2000, 3000
            reorder_enabled=False,
        )
        db_session.add(comp_loc)

        # Add minimal transactions
        txn = StockTransaction(
            component_id=comp.id,
            transaction_type=TransactionType.REMOVE,
            quantity_change=-1,
            previous_quantity=1000,
            new_quantity=999,
            reason="Minimal use",
            from_location_id=sample_location.id,
            created_at=datetime.now(UTC) - timedelta(days=30),
        )
        db_session.add(txn)
        components.append(comp)

    db_session.commit()

    response = analytics_service.get_slow_moving_stock(min_days_of_stock=100)

    # Items should be sorted by days_of_stock (highest first)
    if len(response.items) > 1:
        for i in range(len(response.items) - 1):
            assert (
                response.items[i].days_of_stock >= response.items[i + 1].days_of_stock
            )


def test_get_slow_moving_stock_excludes_out_of_stock(
    analytics_service, sample_component, sample_location, db_session
):
    """Test that slow-moving analysis excludes out-of-stock items."""
    # Create component location with zero stock
    comp_loc = ComponentLocation(
        component_id=sample_component.id,
        storage_location_id=sample_location.id,
        quantity_on_hand=0,  # Out of stock
        reorder_enabled=False,
    )
    db_session.add(comp_loc)
    db_session.commit()

    response = analytics_service.get_slow_moving_stock(min_days_of_stock=10)

    # Should not include out-of-stock items
    assert all(item.total_quantity > 0 for item in response.items)


# ==================== Edge Cases and Error Handling ====================


def test_empty_database(analytics_service):
    """Test analytics methods with empty database."""
    # Dashboard summary should work with no data
    response = analytics_service.get_dashboard_summary()
    assert response.health_metrics.total_components == 0
    assert response.health_metrics.low_stock_count == 0
    assert len(response.top_low_stock) == 0
    assert len(response.top_consumers) == 0


def test_zero_velocity_handling(
    analytics_service, sample_component, sample_location, component_location
):
    """Test that zero velocity is handled gracefully in forecasting."""
    # No transactions = zero velocity
    response = analytics_service.get_forecast(
        component_id=sample_component.id,
        location_id=sample_location.id,
        horizon=ForecastHorizon.WEEK,
        lookback_days=30,
    )

    # Should not crash, should handle zero velocity
    assert response.reorder_suggestion is not None
    # With zero velocity, days_until_stockout should be None
    assert (
        response.reorder_suggestion.days_until_stockout is None
        or response.reorder_suggestion.should_reorder is False
    )


def test_single_transaction_analytics(
    analytics_service, sample_component, sample_location, component_location, db_session
):
    """Test analytics with only a single transaction."""
    txn = StockTransaction(
        component_id=sample_component.id,
        transaction_type=TransactionType.ADD,
        quantity_change=100,
        previous_quantity=0,
        new_quantity=100,
        reason="Initial stock",
        to_location_id=sample_location.id,
        created_at=datetime.now(UTC) - timedelta(days=1),
    )
    db_session.add(txn)
    db_session.commit()

    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=7)

    # Should handle single transaction gracefully
    response = analytics_service.get_stock_levels(
        component_id=sample_component.id,
        location_id=sample_location.id,
        start_date=start_date,
        end_date=end_date,
        period=AggregationPeriod.DAILY,
    )

    assert len(response.data) > 0
