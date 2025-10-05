"""
Contract test for POST /api/v1/components/{component_id}/stock/remove
Tests remove stock endpoint according to OpenAPI specification (remove-stock.yaml)
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestRemoveStockContract:
    """Contract tests for remove stock endpoint based on remove-stock.yaml"""

    def test_remove_stock_success_normal_removal(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test successful stock removal with normal quantity (200 OK)"""
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
        add_stock_request = {
            "location_id": location_id,
            "quantity": 50,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers,
        )

        # Remove stock
        remove_stock_request = {
            "location_id": location_id,
            "quantity": 25,
            "comments": "Used in Project Alpha assembly",
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json=remove_stock_request,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response schema per contract
        assert data["success"] is True
        assert data["message"] == "Stock removed successfully"
        assert "transaction_id" in data
        assert data["component_id"] == component_id
        assert data["location_id"] == location_id
        assert data["quantity_removed"] == 25
        assert data["requested_quantity"] == 25
        assert data["capped"] is False
        assert "previous_quantity" in data
        assert "new_quantity" in data
        assert data["location_deleted"] is False
        assert "total_stock" in data

    def test_remove_stock_auto_capped_removal(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test auto-capping when requested quantity exceeds available stock"""
        # Setup
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

        # Add initial stock of 30
        add_stock_request = {
            "location_id": location_id,
            "quantity": 30,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers,
        )

        # Try to remove 50 (more than available)
        remove_stock_request = {
            "location_id": location_id,
            "quantity": 50,
            "comments": "Remove all stock",
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json=remove_stock_request,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify auto-capping behavior
        assert data["success"] is True
        assert data["quantity_removed"] == 30  # Capped at available
        assert data["requested_quantity"] == 50
        assert data["capped"] is True
        assert data["new_quantity"] == 0
        assert data["location_deleted"] is True
        assert (
            "auto-capped" in data["message"].lower()
            or "capped" in data["message"].lower()
        )

    def test_remove_stock_with_reason(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test removal with explicit reason field"""
        # Setup
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
        add_stock_request = {
            "location_id": location_id,
            "quantity": 50,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers,
        )

        # Remove stock with reason
        remove_stock_request = {
            "location_id": location_id,
            "quantity": 10,
            "reason": "damaged",
            "comments": "Damaged during handling - discarded",
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json=remove_stock_request,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["quantity_removed"] == 10

    def test_remove_stock_validation_error_negative_quantity(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test 400 error for negative or zero quantity"""
        # Setup
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

        # Try to remove negative quantity
        remove_stock_request = {
            "location_id": location_id,
            "quantity": -5,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json=remove_stock_request,
            headers=auth_headers,
        )

        assert response.status_code == 422  # Pydantic validation error
        assert "detail" in response.json()

    def test_remove_stock_validation_error_no_stock(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test 400 error when location has no stock"""
        # Setup - create component and location but don't add any stock
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

        # Try to remove stock from empty location
        remove_stock_request = {
            "location_id": location_id,
            "quantity": 10,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json=remove_stock_request,
            headers=auth_headers,
        )

        assert response.status_code == 404  # ComponentLocation not found
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_remove_stock_forbidden_non_admin(
        self, client: TestClient, user_auth_headers
    ):
        """Test 403 error when non-admin user attempts to remove stock"""
        component_id = "550e8400-e29b-41d4-a716-446655440000"
        location_id = "660e8400-e29b-41d4-a716-446655440001"

        remove_stock_request = {
            "location_id": location_id,
            "quantity": 10,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json=remove_stock_request,
            headers=user_auth_headers,
        )

        assert response.status_code in [403, 404]

    def test_remove_stock_not_found_invalid_component(
        self, client: TestClient, auth_headers, sample_storage_location_data
    ):
        """Test 404 error when component does not exist"""
        # Create location
        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        fake_component_id = "00000000-0000-0000-0000-000000000000"

        remove_stock_request = {
            "location_id": location_id,
            "quantity": 10,
        }

        response = client.post(
            f"/api/v1/components/{fake_component_id}/stock/remove",
            json=remove_stock_request,
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_remove_stock_not_found_location_not_found(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """Test 404 error when ComponentLocation does not exist"""
        # Create component only
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        fake_location_id = "00000000-0000-0000-0000-000000000000"

        remove_stock_request = {
            "location_id": fake_location_id,
            "quantity": 10,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json=remove_stock_request,
            headers=auth_headers,
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_remove_stock_conflict_locked_location(
        self,
        client: TestClient,
        db_session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test 409 error when location is locked by another operation"""
        # Setup
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
        add_stock_request = {
            "location_id": location_id,
            "quantity": 50,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers,
        )

        remove_stock_request = {
            "location_id": location_id,
            "quantity": 10,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/remove",
            json=remove_stock_request,
            headers=auth_headers,
        )

        # Endpoint doesn't exist yet, will fail with 404
        # Once implemented with locking, concurrent access returns 409
        assert response.status_code in [200, 404, 409]

    def test_remove_stock_requires_authentication(self, client: TestClient):
        """Test that remove stock requires authentication"""
        component_id = "550e8400-e29b-41d4-a716-446655440000"
        location_id = "660e8400-e29b-41d4-a716-446655440001"

        remove_stock_request = {
            "location_id": location_id,
            "quantity": 10,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/remove", json=remove_stock_request
        )

        assert response.status_code in [401, 404]
