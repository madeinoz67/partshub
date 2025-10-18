"""
Contract tests for reorder alerts API endpoints.
Tests all endpoints according to OpenAPI specification.

Endpoints tested:
- GET /api/v1/reorder-alerts/ - List active alerts
- GET /api/v1/reorder-alerts/history - Historical alerts
- GET /api/v1/reorder-alerts/{alert_id} - Single alert
- POST /api/v1/reorder-alerts/{alert_id}/dismiss - Dismiss alert
- POST /api/v1/reorder-alerts/{alert_id}/mark-ordered - Mark as ordered
- PUT /api/v1/reorder-alerts/thresholds/{component_id}/{location_id} - Update threshold
- POST /api/v1/reorder-alerts/thresholds/bulk - Bulk threshold updates
- GET /api/v1/reorder-alerts/reports/low-stock - Low stock report
- GET /api/v1/reorder-alerts/reports/statistics - Alert statistics
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestReorderAlertsContract:
    """Contract tests for reorder alerts endpoints"""

    # ==================== Alert Retrieval ====================

    def test_list_active_alerts_success(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test GET /api/v1/reorder-alerts/ returns active alerts (200 OK)"""
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

        # Add stock with reorder threshold
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 10},
            headers=auth_headers,
        )

        # Set reorder threshold above current stock (triggers alert)
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        # List active alerts
        response = client.get("/api/v1/reorder-alerts/", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total_count" in data
        assert isinstance(data["alerts"], list)
        assert data["total_count"] >= 1

        # Verify alert structure
        if data["alerts"]:
            alert = data["alerts"][0]
            assert "id" in alert
            assert "component_id" in alert
            assert "component_name" in alert
            assert "location_id" in alert
            assert "location_name" in alert
            assert "status" in alert
            assert alert["status"] == "active"
            assert "severity" in alert
            assert "current_quantity" in alert
            assert "reorder_threshold" in alert
            assert "shortage_amount" in alert
            assert "shortage_percentage" in alert

    def test_list_active_alerts_with_filters(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test alert listing with component_id, location_id, and min_shortage filters"""
        # Setup component and location
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

        # Add stock and set threshold
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

        # Filter by component_id
        response = client.get(
            f"/api/v1/reorder-alerts/?component_id={component_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(response.json()["alerts"]) >= 1

        # Filter by location_id
        response = client.get(
            f"/api/v1/reorder-alerts/?location_id={location_id}", headers=auth_headers
        )
        assert response.status_code == 200

        # Filter by min_shortage
        response = client.get(
            "/api/v1/reorder-alerts/?min_shortage=30", headers=auth_headers
        )
        assert response.status_code == 200

    def test_get_alert_history_success(self, client: TestClient, auth_headers):
        """Test GET /api/v1/reorder-alerts/history returns historical alerts (200 OK)"""
        response = client.get("/api/v1/reorder-alerts/history", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert "total_count" in data
        assert isinstance(data["alerts"], list)

    def test_get_alert_by_id_success(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test GET /api/v1/reorder-alerts/{alert_id} returns single alert (200 OK)"""
        # Create alert by setting threshold below stock
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
            json={"location_id": location_id, "quantity": 5},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 20, "enabled": True},
            headers=auth_headers,
        )

        # Get alert ID from list
        alerts_resp = client.get("/api/v1/reorder-alerts/", headers=auth_headers)
        alerts = alerts_resp.json()["alerts"]
        if alerts:
            alert_id = alerts[0]["id"]

            # Get single alert
            response = client.get(
                f"/api/v1/reorder-alerts/{alert_id}", headers=auth_headers
            )
            assert response.status_code == 200
            alert = response.json()
            assert alert["id"] == alert_id
            assert "component_id" in alert
            assert "status" in alert

    def test_get_alert_not_found(self, client: TestClient, auth_headers):
        """Test GET /api/v1/reorder-alerts/{alert_id} returns 404 for non-existent alert"""
        response = client.get("/api/v1/reorder-alerts/999999", headers=auth_headers)
        assert response.status_code == 404
        assert "detail" in response.json()

    # ==================== Alert Lifecycle ====================

    def test_dismiss_alert_success(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test POST /api/v1/reorder-alerts/{alert_id}/dismiss succeeds (200 OK)"""
        # Create alert
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
            json={"location_id": location_id, "quantity": 5},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 20, "enabled": True},
            headers=auth_headers,
        )

        # Get alert ID
        alerts_resp = client.get("/api/v1/reorder-alerts/", headers=auth_headers)
        alerts = alerts_resp.json()["alerts"]
        if alerts:
            alert_id = alerts[0]["id"]

            # Dismiss alert
            response = client.post(
                f"/api/v1/reorder-alerts/{alert_id}/dismiss",
                json={"notes": "Component being phased out"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "dismissed"
            assert data["notes"] == "Component being phased out"
            assert "dismissed_at" in data

    def test_dismiss_alert_already_dismissed(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test dismissing already dismissed alert returns 400"""
        # Create and dismiss alert
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
            json={"location_id": location_id, "quantity": 5},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 20, "enabled": True},
            headers=auth_headers,
        )

        alerts_resp = client.get("/api/v1/reorder-alerts/", headers=auth_headers)
        alerts = alerts_resp.json()["alerts"]
        if alerts:
            alert_id = alerts[0]["id"]

            # Dismiss once
            client.post(
                f"/api/v1/reorder-alerts/{alert_id}/dismiss",
                json={},
                headers=auth_headers,
            )

            # Try to dismiss again
            response = client.post(
                f"/api/v1/reorder-alerts/{alert_id}/dismiss",
                json={},
                headers=auth_headers,
            )
            assert response.status_code == 400

    def test_mark_alert_ordered_success(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test POST /api/v1/reorder-alerts/{alert_id}/mark-ordered succeeds (200 OK)"""
        # Create alert
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
            json={"location_id": location_id, "quantity": 5},
            headers=auth_headers,
        )
        client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 20, "enabled": True},
            headers=auth_headers,
        )

        alerts_resp = client.get("/api/v1/reorder-alerts/", headers=auth_headers)
        alerts = alerts_resp.json()["alerts"]
        if alerts:
            alert_id = alerts[0]["id"]

            # Mark as ordered
            response = client.post(
                f"/api/v1/reorder-alerts/{alert_id}/mark-ordered",
                json={"notes": "PO-2025-042 placed with Mouser"},
                headers=auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ordered"
            assert "ordered_at" in data
            assert data["notes"] == "PO-2025-042 placed with Mouser"

    # ==================== Threshold Management ====================

    def test_update_threshold_success(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test PUT /api/v1/reorder-alerts/thresholds/{comp}/{loc} succeeds (200 OK)"""
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

        # Add stock first
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Update threshold
        response = client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["reorder_threshold"] == 50
        assert data["reorder_enabled"] is True
        assert data["current_quantity"] == 100
        assert data["needs_reorder"] is False  # Stock (100) > threshold (50)

    def test_update_threshold_triggers_alert(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test updating threshold above stock level triggers alert creation"""
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

        # Add low stock
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 10},
            headers=auth_headers,
        )

        # Set threshold above stock (should trigger alert)
        response = client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 50, "enabled": True},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["needs_reorder"] is True

        # Verify alert was created
        alerts_resp = client.get(
            f"/api/v1/reorder-alerts/?component_id={component_id}",
            headers=auth_headers,
        )
        alerts = alerts_resp.json()["alerts"]
        assert len(alerts) >= 1

    def test_update_threshold_disable_monitoring(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test disabling reorder monitoring with enabled=False"""
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
            json={"location_id": location_id, "quantity": 5},
            headers=auth_headers,
        )

        # Disable monitoring
        response = client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": 0, "enabled": False},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["reorder_enabled"] is False
        assert response.json()["needs_reorder"] is False

    def test_update_threshold_validation_negative(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test 400 error for negative threshold value"""
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

        response = client.put(
            f"/api/v1/reorder-alerts/thresholds/{component_id}/{location_id}",
            json={"threshold": -10, "enabled": True},
            headers=auth_headers,
        )

        assert response.status_code == 422  # Pydantic validation

    def test_bulk_threshold_updates_success(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test POST /api/v1/reorder-alerts/thresholds/bulk succeeds (200 OK)"""
        # Create two component locations (need unique part_number for each)
        comp1_resp = client.post(
            "/api/v1/components",
            json={
                **sample_component_data,
                "name": "Component 1",
                "part_number": "PN-001",
            },
            headers=auth_headers,
        )
        comp1_id = comp1_resp.json()["id"]

        comp2_resp = client.post(
            "/api/v1/components",
            json={
                **sample_component_data,
                "name": "Component 2",
                "part_number": "PN-002",
            },
            headers=auth_headers,
        )
        comp2_id = comp2_resp.json()["id"]

        loc_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        loc_id = loc_resp.json()["id"]

        # Add stock
        client.post(
            f"/api/v1/components/{comp1_id}/stock/add",
            json={"location_id": loc_id, "quantity": 50},
            headers=auth_headers,
        )
        client.post(
            f"/api/v1/components/{comp2_id}/stock/add",
            json={"location_id": loc_id, "quantity": 75},
            headers=auth_headers,
        )

        # Bulk update
        response = client.post(
            "/api/v1/reorder-alerts/thresholds/bulk",
            json={
                "updates": [
                    {
                        "component_id": comp1_id,
                        "location_id": loc_id,
                        "threshold": 30,
                        "enabled": True,
                    },
                    {
                        "component_id": comp2_id,
                        "location_id": loc_id,
                        "threshold": 40,
                        "enabled": True,
                    },
                ]
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 2
        assert data["error_count"] == 0

    # ==================== Reports ====================

    def test_low_stock_report_success(self, client: TestClient, auth_headers):
        """Test GET /api/v1/reorder-alerts/reports/low-stock returns report (200 OK)"""
        response = client.get(
            "/api/v1/reorder-alerts/reports/low-stock", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total_count" in data
        assert isinstance(data["items"], list)

    def test_alert_statistics_success(self, client: TestClient, auth_headers):
        """Test GET /api/v1/reorder-alerts/reports/statistics returns stats (200 OK)"""
        response = client.get(
            "/api/v1/reorder-alerts/reports/statistics", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "by_status" in data
        assert "active_alerts" in data
        assert isinstance(data["by_status"], dict)
        assert isinstance(data["active_alerts"], dict)

    # ==================== Authentication & Authorization ====================

    def test_requires_authentication(self, client: TestClient):
        """Test all endpoints require authentication (401 Unauthorized)"""
        endpoints = [
            ("GET", "/api/v1/reorder-alerts/"),
            ("GET", "/api/v1/reorder-alerts/history"),
            ("GET", "/api/v1/reorder-alerts/1"),
            ("POST", "/api/v1/reorder-alerts/1/dismiss"),
            ("POST", "/api/v1/reorder-alerts/1/mark-ordered"),
            ("GET", "/api/v1/reorder-alerts/reports/low-stock"),
            ("GET", "/api/v1/reorder-alerts/reports/statistics"),
        ]

        for method, endpoint in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})
            assert response.status_code == 401

    def test_requires_admin(self, client: TestClient, user_auth_headers):
        """Test all endpoints require admin role (403 Forbidden)"""
        endpoints = [
            ("GET", "/api/v1/reorder-alerts/"),
            ("GET", "/api/v1/reorder-alerts/reports/low-stock"),
        ]

        for method, endpoint in endpoints:
            response = client.get(endpoint, headers=user_auth_headers)
            assert response.status_code == 403
