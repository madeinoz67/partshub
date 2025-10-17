"""
Integration tests for analytics API endpoints.

Tests all five analytics endpoints with real database operations:
- GET /api/v1/analytics/stock-levels - Time-series stock data
- GET /api/v1/analytics/usage-trends - Consumption patterns
- GET /api/v1/analytics/forecast - Stock predictions
- GET /api/v1/analytics/dashboard - Inventory KPIs
- GET /api/v1/analytics/slow-moving-stock - Slow movers

Tests cover:
- Happy path scenarios with valid data
- Edge cases (no data, single transaction, zero velocity)
- Authorization (admin-only access)
- Date range filtering
- Location filtering
- Aggregation periods (daily, weekly, monthly)
- Forecast horizons and lookback periods
"""

from datetime import UTC, datetime, timedelta

import pytest


@pytest.mark.integration
class TestAnalyticsStockLevels:
    """Integration tests for stock levels time-series endpoint"""

    def test_get_stock_levels_with_transactions(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test stock levels endpoint returns time-series data with transactions"""
        # Create component and location
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add stock transactions over time
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Get stock levels for last 30 days
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=30)

        response = client.get(
            "/api/v1/analytics/stock-levels",
            params={
                "component_id": component_id,
                "location_id": location_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "period": "daily",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["component_id"] == component_id
        assert data["component_name"] == sample_component_data["name"]
        assert data["location_id"] == location_id
        assert data["period"] == "daily"
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

        # Verify data points
        for point in data["data"]:
            assert "timestamp" in point
            assert "quantity" in point
            assert "transaction_count" in point
            assert point["quantity"] >= 0

        # Verify metadata
        assert "metadata" in data
        assert data["metadata"]["current_quantity"] == 100

    def test_get_stock_levels_aggregation_periods(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test different aggregation periods (daily, weekly, monthly)"""
        # Create component and add stock
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=90)

        # Test each aggregation period
        for period in ["daily", "weekly", "monthly"]:
            response = client.get(
                "/api/v1/analytics/stock-levels",
                params={
                    "component_id": component_id,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "period": period,
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["period"] == period

    def test_get_stock_levels_all_locations(
        self,
        client,
        auth_headers,
        sample_component_data,
    ):
        """Test stock levels aggregated across all locations"""
        # Create component and two locations
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        loc1_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location 1", "type": "drawer"},
            headers=auth_headers,
        )
        loc1_id = loc1_resp.json()["id"]

        loc2_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location 2", "type": "drawer"},
            headers=auth_headers,
        )
        loc2_id = loc2_resp.json()["id"]

        # Add stock to both locations
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": loc1_id, "quantity": 50},
            headers=auth_headers,
        )
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": loc2_id, "quantity": 75},
            headers=auth_headers,
        )

        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=7)

        # Get aggregated stock levels (no location_id)
        response = client.get(
            "/api/v1/analytics/stock-levels",
            params={
                "component_id": component_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "period": "daily",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["location_id"] is None
        assert data["location_name"] is None
        assert data["metadata"]["current_quantity"] == 125  # 50 + 75

    def test_get_stock_levels_component_not_found(self, client, auth_headers):
        """Test 404 error for non-existent component"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=7)

        response = client.get(
            "/api/v1/analytics/stock-levels",
            params={
                "component_id": fake_uuid,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 404

    def test_get_stock_levels_requires_admin(self, client, user_auth_headers):
        """Test that stock levels endpoint requires admin authentication"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=7)

        response = client.get(
            "/api/v1/analytics/stock-levels",
            params={
                "component_id": fake_uuid,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=user_auth_headers,
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestAnalyticsUsageTrends:
    """Integration tests for usage trends endpoint"""

    def test_get_usage_trends_with_consumption(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test usage trends returns consumption data and velocity metrics"""
        # Create component and location
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add initial stock
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Remove stock to create consumption
        client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json={"location_id": location_id, "quantity": 25, "reason": "usage"},
            headers=auth_headers,
        )

        # Get usage trends
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=30)

        response = client.get(
            "/api/v1/analytics/usage-trends",
            params={
                "component_id": component_id,
                "location_id": location_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "period": "daily",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["component_id"] == component_id
        assert data["period"] == "daily"
        assert isinstance(data["data"], list)

        # Verify velocity metrics
        velocity = data["velocity"]
        assert "daily_average" in velocity
        assert "weekly_average" in velocity
        assert "monthly_average" in velocity
        assert "total_consumed" in velocity
        assert "days_analyzed" in velocity
        assert velocity["total_consumed"] == 25

        # Verify usage data points
        for point in data["data"]:
            assert "timestamp" in point
            assert "consumed" in point
            assert "added" in point
            assert "removed" in point

    def test_get_usage_trends_zero_velocity(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test usage trends with no consumption (zero velocity)"""
        # Create component with stock but no removals
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Get usage trends (should show zero velocity)
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=7)

        response = client.get(
            "/api/v1/analytics/usage-trends",
            params={
                "component_id": component_id,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify zero velocity
        velocity = data["velocity"]
        assert velocity["total_consumed"] == 0
        assert velocity["daily_average"] == 0.0

    def test_get_usage_trends_requires_admin(self, client, user_auth_headers):
        """Test that usage trends endpoint requires admin authentication"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=7)

        response = client.get(
            "/api/v1/analytics/usage-trends",
            params={
                "component_id": fake_uuid,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
            headers=user_auth_headers,
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestAnalyticsForecast:
    """Integration tests for stock forecast endpoint"""

    def test_get_forecast_with_consumption(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test forecast generates predictions based on historical consumption"""
        # Create component with consumption history
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add stock and simulate consumption
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )
        client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json={"location_id": location_id, "quantity": 20, "reason": "usage"},
            headers=auth_headers,
        )

        # Get forecast
        response = client.get(
            "/api/v1/analytics/forecast",
            params={
                "component_id": component_id,
                "location_id": location_id,
                "horizon": "14d",
                "lookback_days": 30,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["component_id"] == component_id
        assert data["current_quantity"] == 80
        assert data["forecast_horizon"] == "14d"
        assert data["lookback_days"] == 30

        # Verify forecast data points
        assert len(data["data"]) == 14  # 14 days
        for point in data["data"]:
            assert "timestamp" in point
            assert "predicted_quantity" in point
            assert "confidence_level" in point
            assert "will_trigger_reorder" in point
            assert 0.0 <= point["confidence_level"] <= 1.0

        # Verify reorder suggestion
        suggestion = data["reorder_suggestion"]
        assert "should_reorder" in suggestion
        assert "confidence_level" in suggestion

        # Verify metadata
        assert data["metadata"]["algorithm"] == "simple_moving_average"
        assert "daily_velocity" in data["metadata"]

    def test_get_forecast_different_horizons(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test different forecast horizons (7d, 14d, 30d, 90d)"""
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Test each horizon
        for horizon, expected_days in [
            ("7d", 7),
            ("14d", 14),
            ("30d", 30),
            ("90d", 90),
        ]:
            response = client.get(
                "/api/v1/analytics/forecast",
                params={
                    "component_id": component_id,
                    "horizon": horizon,
                    "lookback_days": 30,
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["forecast_horizon"] == horizon
            assert len(data["data"]) == expected_days

    def test_get_forecast_with_reorder_threshold(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test forecast reorder suggestions with threshold configured"""
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add stock and set reorder threshold
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 50},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 40, "enabled": True},
            headers=auth_headers,
        )

        # Remove stock to create velocity
        client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json={"location_id": location_id, "quantity": 5, "reason": "usage"},
            headers=auth_headers,
        )

        # Get forecast
        response = client.get(
            "/api/v1/analytics/forecast",
            params={
                "component_id": component_id,
                "location_id": location_id,
                "horizon": "30d",
                "lookback_days": 30,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify reorder threshold is included
        assert data["reorder_threshold"] == 40

        # Verify forecast points check against threshold
        for point in data["data"]:
            if point["predicted_quantity"] < 40:
                assert point["will_trigger_reorder"] is True

    def test_get_forecast_requires_admin(self, client, user_auth_headers):
        """Test that forecast endpoint requires admin authentication"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            "/api/v1/analytics/forecast",
            params={"component_id": fake_uuid},
            headers=user_auth_headers,
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestAnalyticsDashboard:
    """Integration tests for dashboard summary endpoint"""

    def test_get_dashboard_summary_basic(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test dashboard summary returns inventory health metrics"""
        # Create component with stock
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Get dashboard summary
        response = client.get(
            "/api/v1/analytics/dashboard",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify health metrics
        health = data["health_metrics"]
        assert "total_components" in health
        assert "low_stock_count" in health
        assert "out_of_stock_count" in health
        assert "total_inventory_value" in health
        assert "active_alerts_count" in health
        assert "average_stock_velocity" in health
        assert health["total_components"] >= 1

        # Verify top lists
        assert "top_low_stock" in data
        assert "top_consumers" in data
        assert isinstance(data["top_low_stock"], list)
        assert isinstance(data["top_consumers"], list)

        # Verify recent activity count
        assert "recent_activity_count" in data
        assert data["recent_activity_count"] >= 0

        # Verify metadata
        assert "metadata" in data
        assert "last_updated" in data["metadata"]

    def test_get_dashboard_summary_with_low_stock(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test dashboard identifies low stock components"""
        # Create component with low stock
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add low stock and enable reorder
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 10},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        db_session.commit()

        # Get dashboard
        response = client.get(
            "/api/v1/analytics/dashboard",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify low stock is detected
        health = data["health_metrics"]
        assert health["low_stock_count"] >= 1
        assert health["active_alerts_count"] >= 1

        # Verify component appears in top_low_stock
        if data["top_low_stock"]:
            low_stock_item = data["top_low_stock"][0]
            assert "component_id" in low_stock_item
            assert "component_name" in low_stock_item
            assert "total_quantity" in low_stock_item
            assert "has_active_alerts" in low_stock_item
            assert "daily_velocity" in low_stock_item

    def test_get_dashboard_summary_requires_admin(self, client, user_auth_headers):
        """Test that dashboard endpoint requires admin authentication"""
        response = client.get(
            "/api/v1/analytics/dashboard",
            headers=user_auth_headers,
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestAnalyticsSlowMovingStock:
    """Integration tests for slow-moving stock endpoint"""

    def test_get_slow_moving_stock_basic(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test slow-moving stock identifies components with high days of stock"""
        # Create component with high stock and zero velocity
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add large quantity (will have high days of stock due to zero consumption)
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 1000},
            headers=auth_headers,
        )

        # Get slow-moving stock
        response = client.get(
            "/api/v1/analytics/slow-moving-stock",
            params={"min_days_of_stock": 100},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "items" in data
        assert "total_count" in data
        assert "total_value_locked" in data
        assert "metadata" in data

        # Verify metadata
        assert data["metadata"]["min_days_of_stock"] == 100

    def test_get_slow_moving_stock_with_velocity(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test slow-moving calculation with low velocity"""
        # Create component with stock and minimal consumption
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add stock
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 500},
            headers=auth_headers,
        )

        # Very small consumption (creates low velocity, high days of stock)
        client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json={"location_id": location_id, "quantity": 1, "reason": "usage"},
            headers=auth_headers,
        )

        # Get slow-moving stock
        response = client.get(
            "/api/v1/analytics/slow-moving-stock",
            params={"min_days_of_stock": 180},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should find the slow-moving component
        if data["items"]:
            item = data["items"][0]
            assert "component_id" in item
            assert "component_name" in item
            assert "total_quantity" in item
            assert "daily_velocity" in item
            assert "days_of_stock" in item
            assert item["days_of_stock"] >= 180

    def test_get_slow_moving_stock_days_since_last_use_filter(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test slow-moving stock filter by days since last use"""
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 1000},
            headers=auth_headers,
        )

        # Get slow-moving with days_since_last_use filter
        response = client.get(
            "/api/v1/analytics/slow-moving-stock",
            params={"min_days_of_stock": 180, "min_days_since_last_use": 90},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify filter is applied
        assert data["metadata"]["min_days_since_last_use"] == 90

    def test_get_slow_moving_stock_requires_admin(self, client, user_auth_headers):
        """Test that slow-moving stock endpoint requires admin authentication"""
        response = client.get(
            "/api/v1/analytics/slow-moving-stock",
            headers=user_auth_headers,
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestAnalyticsAuthorization:
    """Test authorization for all analytics endpoints"""

    def test_all_endpoints_require_authentication(self, client):
        """Test that all analytics endpoints require authentication"""
        endpoints = [
            "/api/v1/analytics/stock-levels",
            "/api/v1/analytics/usage-trends",
            "/api/v1/analytics/forecast",
            "/api/v1/analytics/dashboard",
            "/api/v1/analytics/slow-moving-stock",
        ]

        fake_uuid = "00000000-0000-0000-0000-000000000000"
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=7)

        for endpoint in endpoints:
            if endpoint in [
                "/api/v1/analytics/dashboard",
                "/api/v1/analytics/slow-moving-stock",
            ]:
                # These don't require date params
                response = client.get(endpoint)
            elif endpoint == "/api/v1/analytics/forecast":
                # Forecast requires different params
                response = client.get(endpoint, params={"component_id": fake_uuid})
            else:
                # Stock levels and usage trends require date params
                response = client.get(
                    endpoint,
                    params={
                        "component_id": fake_uuid,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                )

            assert (
                response.status_code == 401
            ), f"Endpoint {endpoint} should require authentication"

    def test_all_endpoints_require_admin_role(self, client, user_auth_headers):
        """Test that all analytics endpoints require admin role"""
        endpoints = [
            "/api/v1/analytics/stock-levels",
            "/api/v1/analytics/usage-trends",
            "/api/v1/analytics/forecast",
            "/api/v1/analytics/dashboard",
            "/api/v1/analytics/slow-moving-stock",
        ]

        fake_uuid = "00000000-0000-0000-0000-000000000000"
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=7)

        for endpoint in endpoints:
            if endpoint in [
                "/api/v1/analytics/dashboard",
                "/api/v1/analytics/slow-moving-stock",
            ]:
                response = client.get(endpoint, headers=user_auth_headers)
            elif endpoint == "/api/v1/analytics/forecast":
                response = client.get(
                    endpoint,
                    params={"component_id": fake_uuid},
                    headers=user_auth_headers,
                )
            else:
                response = client.get(
                    endpoint,
                    params={
                        "component_id": fake_uuid,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                    headers=user_auth_headers,
                )

            assert (
                response.status_code == 403
            ), f"Endpoint {endpoint} should require admin role"


@pytest.mark.integration
class TestAnalyticsInventorySummary:
    """Integration tests for inventory summary endpoint"""

    def test_get_inventory_summary_basic(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test inventory summary returns aggregate KPIs"""
        # Create component with stock
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Get inventory summary
        response = client.get(
            "/api/v1/analytics/inventory-summary",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total_components" in data
        assert "total_stock_value" in data
        assert "low_stock_count" in data
        assert "out_of_stock_count" in data
        assert "overstocked_count" in data
        assert "average_stock_level_percentage" in data
        assert "total_locations" in data
        assert "metadata" in data

        # Verify values are reasonable
        assert data["total_components"] >= 1
        assert data["total_stock_value"] >= 0
        assert data["total_locations"] >= 1

    def test_get_inventory_summary_with_low_stock(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test inventory summary identifies low stock correctly"""
        # Create component with low stock
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add stock below threshold
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 10},
            headers=auth_headers,
        )

        # Set high threshold to trigger low stock
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        db_session.commit()

        # Get summary
        response = client.get(
            "/api/v1/analytics/inventory-summary",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify low stock is detected
        assert data["low_stock_count"] >= 1
        assert data["out_of_stock_count"] == 0

    def test_get_inventory_summary_with_overstocked(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test inventory summary identifies overstocked components"""
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add stock well above threshold (>= 1.5x)
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 200},
            headers=auth_headers,
        )

        # Set low threshold
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        db_session.commit()

        # Get summary
        response = client.get(
            "/api/v1/analytics/inventory-summary",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify overstocked is detected (200 >= 50 * 1.5 = 75)
        assert data["overstocked_count"] >= 1

    def test_get_inventory_summary_requires_admin(self, client, user_auth_headers):
        """Test that inventory summary endpoint requires admin authentication"""
        response = client.get(
            "/api/v1/analytics/inventory-summary",
            headers=user_auth_headers,
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestAnalyticsStockDistribution:
    """Integration tests for stock distribution endpoint"""

    def test_get_stock_distribution_basic(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test stock distribution returns category breakdown"""
        # Create component with stock
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Get stock distribution
        response = client.get(
            "/api/v1/analytics/stock-distribution",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "total_components" in data
        assert "distribution" in data
        assert "timestamp" in data
        assert data["total_components"] >= 1
        assert isinstance(data["distribution"], list)
        assert len(data["distribution"]) == 4  # 4 status categories

        # Verify each distribution item
        for item in data["distribution"]:
            assert "status" in item
            assert "count" in item
            assert "percentage" in item
            assert item["status"] in ["critical", "low", "ok", "overstocked"]
            assert item["count"] >= 0
            assert 0 <= item["percentage"] <= 100

        # Verify percentages sum to 100 (or close due to rounding)
        total_percentage = sum(item["percentage"] for item in data["distribution"])
        assert 99.9 <= total_percentage <= 100.1

    def test_get_stock_distribution_multiple_components(
        self,
        client,
        db_session,
        auth_headers,
        sample_component_data,
    ):
        """Test stock distribution with multiple components in different states"""
        location_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Test Location", "type": "drawer"},
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Create LOW component (below threshold)
        comp2_resp = client.post(
            "/api/v1/components",
            json={"name": "Low Component", "category": "Capacitors"},
            headers=auth_headers,
        )
        comp2_id = comp2_resp.json()["id"]
        client.post(
            f"/api/v1/components/{comp2_id}/stock/add",
            json={"location_id": location_id, "quantity": 10},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{comp2_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        # Create OK component (above threshold but < 1.5x)
        comp3_resp = client.post(
            "/api/v1/components",
            json={"name": "OK Component", "category": "ICs"},
            headers=auth_headers,
        )
        comp3_id = comp3_resp.json()["id"]
        client.post(
            f"/api/v1/components/{comp3_id}/stock/add",
            json={"location_id": location_id, "quantity": 60},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{comp3_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        # Create OVERSTOCKED component (>= 1.5x threshold)
        comp4_resp = client.post(
            "/api/v1/components",
            json={"name": "Overstocked Component", "category": "Diodes"},
            headers=auth_headers,
        )
        comp4_id = comp4_resp.json()["id"]
        client.post(
            f"/api/v1/components/{comp4_id}/stock/add",
            json={"location_id": location_id, "quantity": 200},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{comp4_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        db_session.commit()

        # Get distribution
        response = client.get(
            "/api/v1/analytics/stock-distribution",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify we have the expected components in their categories
        status_counts = {item["status"]: item["count"] for item in data["distribution"]}
        assert status_counts["low"] >= 1
        assert status_counts["ok"] >= 1
        assert status_counts["overstocked"] >= 1
        # Total should be at least 3
        assert data["total_components"] >= 3

    def test_get_stock_distribution_requires_admin(self, client, user_auth_headers):
        """Test that stock distribution endpoint requires admin authentication"""
        response = client.get(
            "/api/v1/analytics/stock-distribution",
            headers=user_auth_headers,
        )

        assert response.status_code == 403


@pytest.mark.integration
class TestAnalyticsTopVelocity:
    """Integration tests for top velocity endpoint"""

    def test_get_top_velocity_basic(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test top velocity returns fastest-moving components"""
        # Create component with consumption
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Add stock
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Create multiple removal transactions to establish velocity
        client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json={"location_id": location_id, "quantity": 10, "reason": "usage"},
            headers=auth_headers,
        )
        client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json={"location_id": location_id, "quantity": 15, "reason": "usage"},
            headers=auth_headers,
        )

        # Get top velocity
        response = client.get(
            "/api/v1/analytics/top-velocity",
            params={"limit": 10, "lookback_days": 30, "min_transactions": 2},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "components" in data
        assert "period_analyzed" in data
        assert "total_components_analyzed" in data
        assert "metadata" in data
        assert isinstance(data["components"], list)

        # If we have velocity components, verify structure
        if data["components"]:
            component = data["components"][0]
            assert "component_id" in component
            assert "component_name" in component
            assert "part_number" in component
            assert "daily_velocity" in component
            assert "weekly_velocity" in component
            assert "monthly_velocity" in component
            assert "current_quantity" in component
            assert "days_until_stockout" in component
            assert "location_name" in component

            # Verify velocity values are positive
            assert component["daily_velocity"] > 0
            assert component["weekly_velocity"] > 0
            assert component["monthly_velocity"] > 0

    def test_get_top_velocity_with_parameters(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test top velocity with different query parameters"""
        # Create component with consumption
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Create transactions
        for _ in range(5):
            client.post(
                f"/api/v1/components/{component_id}/stock/remove",
                json={"location_id": location_id, "quantity": 5, "reason": "usage"},
                headers=auth_headers,
            )

        # Test with custom parameters
        response = client.get(
            "/api/v1/analytics/top-velocity",
            params={"limit": 5, "lookback_days": 7, "min_transactions": 3},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify metadata reflects our parameters
        assert data["metadata"]["limit"] == 5
        assert data["metadata"]["lookback_days"] == 7
        assert data["metadata"]["min_transactions"] == 3
        assert data["period_analyzed"] == "last_7_days"

    def test_get_top_velocity_min_transactions_filter(
        self,
        client,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test top velocity filters by minimum transactions"""
        # Create component with only 1 transaction (below min_transactions=2)
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Single transaction (should be filtered out)
        client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json={"location_id": location_id, "quantity": 10, "reason": "usage"},
            headers=auth_headers,
        )

        # Get top velocity with min_transactions=2
        response = client.get(
            "/api/v1/analytics/top-velocity",
            params={"min_transactions": 2},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Component should not appear in results (only 1 transaction)
        component_ids = [comp["component_id"] for comp in data["components"]]
        assert component_id not in component_ids

    def test_get_top_velocity_empty_inventory(self, client, auth_headers):
        """Test top velocity with empty inventory"""
        response = client.get(
            "/api/v1/analytics/top-velocity",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return empty list
        assert data["components"] == []
        assert data["total_components_analyzed"] >= 0

    def test_get_top_velocity_requires_admin(self, client, user_auth_headers):
        """Test that top velocity endpoint requires admin authentication"""
        response = client.get(
            "/api/v1/analytics/top-velocity",
            headers=user_auth_headers,
        )

        assert response.status_code == 403
