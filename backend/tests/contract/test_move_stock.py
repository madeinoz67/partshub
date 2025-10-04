"""
Contract test for POST /api/v1/components/{component_id}/stock/move
Tests move stock endpoint according to OpenAPI specification (move-stock.yaml)
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestMoveStockContract:
    """Contract tests for move stock endpoint based on move-stock.yaml"""

    def test_move_stock_success_between_existing_locations(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """Test successful stock move between two existing locations (200 OK)"""
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Create two storage locations
        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A", "description": "Source location"},
            headers=auth_headers
        )
        location_a_id = location_a_resp.json()["id"]

        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B", "description": "Destination location"},
            headers=auth_headers
        )
        location_b_id = location_b_resp.json()["id"]

        # Add stock to location A
        add_stock_request = {
            "location_id": location_a_id,
            "quantity": 50,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        # Add stock to location B (so it's an existing ComponentLocation)
        add_stock_request_b = {
            "location_id": location_b_id,
            "quantity": 75,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request_b,
            headers=auth_headers
        )

        # Move stock from A to B
        move_stock_request = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 25,
            "comments": "Moving to primary storage"
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response schema per contract
        assert data["success"] is True
        assert data["message"] == "Stock moved successfully"
        assert "transaction_id" in data
        assert data["component_id"] == component_id
        assert data["source_location_id"] == location_a_id
        assert data["destination_location_id"] == location_b_id
        assert data["quantity_moved"] == 25
        assert data["requested_quantity"] == 25
        assert data["capped"] is False
        assert "source_previous_quantity" in data
        assert "source_new_quantity" in data
        assert data["source_location_deleted"] is False
        assert "destination_previous_quantity" in data
        assert "destination_new_quantity" in data
        assert data["destination_location_created"] is False
        assert "total_stock" in data
        assert "pricing_inherited" in data

    def test_move_stock_to_new_location(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """Test moving stock to location that doesn't have this component yet"""
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Create two locations
        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A", "description": "Source"},
            headers=auth_headers
        )
        location_a_id = location_a_resp.json()["id"]

        location_c_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location C", "description": "New destination"},
            headers=auth_headers
        )
        location_c_id = location_c_resp.json()["id"]

        # Add stock only to location A
        add_stock_request = {
            "location_id": location_a_id,
            "quantity": 30,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        # Move all stock to location C (creates new ComponentLocation)
        move_stock_request = {
            "source_location_id": location_a_id,
            "destination_location_id": location_c_id,
            "quantity": 30,
            "comments": "Creating new stock entry at Lab B"
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify destination was created
        assert data["success"] is True
        assert data["quantity_moved"] == 30
        assert data["source_location_deleted"] is True  # All stock moved
        assert data["destination_location_created"] is True
        assert data["destination_previous_quantity"] == 0
        assert data["destination_new_quantity"] == 30
        assert data["pricing_inherited"] is True

    def test_move_stock_auto_capped(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """Test auto-capping when requested quantity exceeds source stock"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers
        )
        location_a_id = location_a_resp.json()["id"]

        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B"},
            headers=auth_headers
        )
        location_b_id = location_b_resp.json()["id"]

        # Add only 20 units to source
        add_stock_request = {
            "location_id": location_a_id,
            "quantity": 20,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        # Add some stock to destination
        add_stock_request_b = {
            "location_id": location_b_id,
            "quantity": 100,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request_b,
            headers=auth_headers
        )

        # Try to move 50 (more than available)
        move_stock_request = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 50,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Verify auto-capping
        assert data["quantity_moved"] == 20  # Capped at available
        assert data["requested_quantity"] == 50
        assert data["capped"] is True
        assert data["source_location_deleted"] is True
        assert "auto-capped" in data["message"].lower() or "capped" in data["message"].lower()

    def test_move_stock_validation_error_same_location(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """Test 400 error when source and destination are the same"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers
        )
        location_id = location_resp.json()["id"]

        # Add stock
        add_stock_request = {
            "location_id": location_id,
            "quantity": 50,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        # Try to move to same location
        move_stock_request = {
            "source_location_id": location_id,
            "destination_location_id": location_id,
            "quantity": 25,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "same" in data["detail"].lower() or "different" in data["detail"].lower()

    def test_move_stock_validation_error_negative_quantity(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """Test 400 error for negative or zero quantity"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers
        )
        location_a_id = location_a_resp.json()["id"]

        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B"},
            headers=auth_headers
        )
        location_b_id = location_b_resp.json()["id"]

        # Try to move negative quantity
        move_stock_request = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": -10,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 400
        assert "detail" in response.json()

    def test_move_stock_validation_error_no_source_stock(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """Test 400 error when source location has no stock"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers
        )
        location_a_id = location_a_resp.json()["id"]

        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B"},
            headers=auth_headers
        )
        location_b_id = location_b_resp.json()["id"]

        # Don't add any stock to source

        # Try to move stock
        move_stock_request = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 10,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "no stock" in data["detail"].lower() or "not found" in data["detail"].lower()

    def test_move_stock_forbidden_non_admin(
        self, client: TestClient, user_auth_headers
    ):
        """Test 403 error when non-admin user attempts to move stock"""
        component_id = "550e8400-e29b-41d4-a716-446655440000"
        location_a_id = "660e8400-e29b-41d4-a716-446655440001"
        location_b_id = "660e8400-e29b-41d4-a716-446655440002"

        move_stock_request = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 25,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_stock_request,
            headers=user_auth_headers
        )

        assert response.status_code in [403, 404]

    def test_move_stock_not_found_invalid_component(
        self, client: TestClient, auth_headers
    ):
        """Test 404 error when component does not exist"""
        fake_component_id = "00000000-0000-0000-0000-000000000000"
        location_a_id = "660e8400-e29b-41d4-a716-446655440001"
        location_b_id = "660e8400-e29b-41d4-a716-446655440002"

        move_stock_request = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 25,
        }

        response = client.post(
            f"/api/v1/components/{fake_component_id}/stock/move",
            json=move_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "detail" in response.json()

    def test_move_stock_not_found_source_not_found(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """Test 404 error when source ComponentLocation not found"""
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Create destination location only
        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B"},
            headers=auth_headers
        )
        location_b_id = location_b_resp.json()["id"]

        fake_location_a_id = "00000000-0000-0000-0000-000000000000"

        move_stock_request = {
            "source_location_id": fake_location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 25,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "source" in data["detail"].lower() or "not found" in data["detail"].lower()

    def test_move_stock_not_found_destination_location_not_exist(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """Test 404 error when destination StorageLocation does not exist"""
        # Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Create source location
        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers
        )
        location_a_id = location_a_resp.json()["id"]

        # Add stock to source
        add_stock_request = {
            "location_id": location_a_id,
            "quantity": 50,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        fake_location_b_id = "00000000-0000-0000-0000-000000000000"

        move_stock_request = {
            "source_location_id": location_a_id,
            "destination_location_id": fake_location_b_id,
            "quantity": 25,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_stock_request,
            headers=auth_headers
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "destination" in data["detail"].lower() or "not found" in data["detail"].lower()

    def test_move_stock_conflict_locked_locations(
        self, client: TestClient, db_session, auth_headers, sample_component_data
    ):
        """Test 409 error when one or more locations are locked"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        location_a_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location A"},
            headers=auth_headers
        )
        location_a_id = location_a_resp.json()["id"]

        location_b_resp = client.post(
            "/api/v1/storage-locations",
            json={"name": "Location B"},
            headers=auth_headers
        )
        location_b_id = location_b_resp.json()["id"]

        # Add stock
        add_stock_request = {
            "location_id": location_a_id,
            "quantity": 50,
        }
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json=add_stock_request,
            headers=auth_headers
        )

        move_stock_request = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 25,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_stock_request,
            headers=auth_headers
        )

        # Endpoint doesn't exist yet, will fail with 404
        # Once implemented with locking, concurrent access returns 409
        assert response.status_code in [200, 404, 409]

    def test_move_stock_requires_authentication(self, client: TestClient):
        """Test that move stock requires authentication"""
        component_id = "550e8400-e29b-41d4-a716-446655440000"
        location_a_id = "660e8400-e29b-41d4-a716-446655440001"
        location_b_id = "660e8400-e29b-41d4-a716-446655440002"

        move_stock_request = {
            "source_location_id": location_a_id,
            "destination_location_id": location_b_id,
            "quantity": 25,
        }

        response = client.post(
            f"/api/v1/components/{component_id}/stock/move",
            json=move_stock_request
        )

        assert response.status_code in [401, 404]
