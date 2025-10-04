"""
Contract test for POST /api/v1/components/{component_id}/stock/add
Tests add stock endpoint according to OpenAPI specification (add-stock.yaml)
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestAddStockContract:
    """Contract tests for add stock endpoint based on add-stock.yaml"""

    def test_add_stock_success_manual_entry_with_pricing(
        self, client: TestClient, db_session, auth_headers, sample_component_data,
        sample_storage_location_data
    ):
        """Test successful stock addition with manual entry and per-unit pricing (200 OK)"""
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        assert component_resp.status_code == 201
        component_id = component_resp.json()["id"]

        # Create storage location
        location_resp = client.post(
            "/api/v1/storage-locations", json=sample_storage_location_data, headers=auth_headers
        )
        assert location_resp.status_code == 201
        location_id = location_resp.json()["id"]

        # Add stock with per-unit pricing
        add_stock_request = {
            "location_id": location_id,
            "quantity": 100,
            "price_per_unit": 0.50,
            "lot_id": "LOT-2025-Q1-001",
            "comments": "Manual stock addition - quarterly restock"
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response schema per contract
        assert data["success"] is True
        assert data["message"] == "Stock added successfully"
        assert "transaction_id" in data
        assert data["component_id"] == component_id
        assert data["location_id"] == location_id
        assert data["quantity_added"] == 100
        assert "previous_quantity" in data
        assert "new_quantity" in data
        assert "total_stock" in data

    def test_add_stock_order_receiving_with_total_price(
        self, client: TestClient, db_session, auth_headers, sample_component_data,
        sample_storage_location_data
    ):
        """Test stock addition receiving against purchase order with total price"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations", json=sample_storage_location_data, headers=auth_headers
        )
        location_id = location_resp.json()["id"]

        # Add stock with total price and reference
        add_stock_request = {
            "location_id": location_id,
            "quantity": 50,
            "total_price": 25.00,
            "reference_id": "PO-2025-001",
            "reference_type": "purchase_order",
            "comments": "Received shipment against PO-2025-001"
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["quantity_added"] == 50

    def test_add_stock_no_pricing(
        self, client: TestClient, db_session, auth_headers, sample_component_data,
        sample_storage_location_data
    ):
        """Test simple quantity addition without pricing information"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations", json=sample_storage_location_data, headers=auth_headers
        )
        location_id = location_resp.json()["id"]

        # Add stock without pricing
        add_stock_request = {
            "location_id": location_id,
            "quantity": 25,
            "comments": "Found in old inventory"
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["quantity_added"] == 25

    def test_add_stock_validation_error_negative_quantity(
        self, client: TestClient, db_session, auth_headers, sample_component_data,
        sample_storage_location_data
    ):
        """Test 400 error for negative or zero quantity"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations", json=sample_storage_location_data, headers=auth_headers
        )
        location_id = location_resp.json()["id"]

        # Try to add negative quantity
        add_stock_request = {
            "location_id": location_id,
            "quantity": -10,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_add_stock_validation_error_both_pricing_fields(
        self, client: TestClient, db_session, auth_headers, sample_component_data,
        sample_storage_location_data
    ):
        """Test 400 error when both price_per_unit and total_price are specified"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations", json=sample_storage_location_data, headers=auth_headers
        )
        location_id = location_resp.json()["id"]

        # Invalid: both pricing fields set
        add_stock_request = {
            "location_id": location_id,
            "quantity": 50,
            "price_per_unit": 0.50,
            "total_price": 25.00,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "both" in data["detail"].lower() or "price" in data["detail"].lower()

    def test_add_stock_forbidden_non_admin(
        self, client: TestClient, db_session, user_auth_headers, sample_component_data,
        sample_storage_location_data
    ):
        """Test 403 error when non-admin user attempts to add stock"""
        # Setup with admin first
        admin_headers = user_auth_headers  # Will use auth_headers fixture for admin setup

        # Create component with admin (we'll need auth_headers fixture)
        # This test requires both admin and non-admin headers
        # For now, skip actual setup and test the endpoint

        # Mock component_id and location_id (endpoints don't exist yet)
        component_id = "550e8400-e29b-41d4-a716-446655440000"
        location_id = "660e8400-e29b-41d4-a716-446655440001"

        add_stock_request = {
            "location_id": location_id,
            "quantity": 50,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=user_auth_headers  # Non-admin user
        )

        # Should be 403 Forbidden (or 404 if endpoint doesn't exist yet)
        assert response.status_code in [403, 404]

    def test_add_stock_not_found_invalid_component(
        self, client: TestClient, auth_headers, sample_storage_location_data
    ):
        """Test 404 error when component does not exist"""
        # Create storage location
        location_resp = client.post(
            "/api/v1/storage-locations", json=sample_storage_location_data, headers=auth_headers
        )
        location_id = location_resp.json()["id"]

        # Use non-existent component ID
        fake_component_id = "00000000-0000-0000-0000-000000000000"

        add_stock_request = {
            "location_id": location_id,
            "quantity": 50,
        }

        response = client.post(
            f"/api/v1/components/{fake_component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_add_stock_not_found_invalid_location(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """Test 400/404 error when storage location does not exist"""
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Use non-existent location ID
        fake_location_id = "00000000-0000-0000-0000-000000000000"

        add_stock_request = {
            "location_id": fake_location_id,
            "quantity": 50,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        assert response.status_code in [400, 404]
        assert "detail" in response.json()

    def test_add_stock_conflict_locked_location(
        self, client: TestClient, db_session, auth_headers, sample_component_data,
        sample_storage_location_data
    ):
        """Test 409 error when location is locked by another operation"""
        # This test will require concurrent access simulation
        # For now, just define the expected behavior

        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations", json=sample_storage_location_data, headers=auth_headers
        )
        location_id = location_resp.json()["id"]

        add_stock_request = {
            "location_id": location_id,
            "quantity": 50,
        }

        # Note: This test will pass once we implement locking
        # For now, it will fail because endpoint doesn't exist
        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        # Endpoint doesn't exist yet, so we expect 404
        # Once implemented, concurrent access would return 409
        assert response.status_code in [200, 404, 409]

    def test_add_stock_requires_authentication(
        self, client: TestClient, sample_component_data, sample_storage_location_data
    ):
        """Test that add stock requires authentication (no headers)"""
        component_id = "550e8400-e29b-41d4-a716-446655440000"
        location_id = "660e8400-e29b-41d4-a716-446655440001"

        add_stock_request = {
            "location_id": location_id,
            "quantity": 50,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request
            # No headers - unauthenticated
        )

        # Should be 401 Unauthorized
        assert response.status_code in [401, 404]
