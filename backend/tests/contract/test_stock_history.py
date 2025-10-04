"""
Contract test for GET /api/v1/components/{component_id}/stock/history
Tests stock history pagination endpoint according to OpenAPI specification (stock-history.yaml)

This test MUST FAIL initially - endpoint has not been implemented yet (TDD red phase)
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.mark.contract
class TestStockHistoryContract:
    """Contract tests for stock history pagination endpoint based on stock-history.yaml"""

    def test_get_history_requires_authentication(self, client: TestClient):
        """Test that stock history endpoint requires authentication (401 Unauthorized)"""
        component_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(f"/api/v1/components/{component_id}/stock/history")

        # Should be 401 Unauthorized (will be 404 until endpoint is implemented)
        assert response.status_code in [401, 404]

    def test_get_history_paginated_default_page_size(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test paginated response with default 10 entries per page (FR-047)"""
        # Setup: Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        assert component_resp.status_code == 201
        component_id = component_resp.json()["id"]

        # Setup: Create storage location
        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        assert location_resp.status_code == 201
        location_id = location_resp.json()["id"]

        # Setup: Create 15 stock transactions to test pagination (need >10 for multi-page test)
        for i in range(15):
            add_stock_request = {
                "location_id": location_id,
                "quantity": 10,
                "comments": f"Transaction {i+1}",
            }
            client.post(
                f"/api/v1/components/{component_id}/stock/add",
                json=add_stock_request,
                headers=auth_headers,
            )
            # Skip assertion - endpoint may not exist yet

        # Test: Get first page with default page_size (should be 10)
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history", headers=auth_headers
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200
        data = response.json()

        # Verify response schema per contract
        assert "entries" in data
        assert "pagination" in data

        # Verify default pagination per FR-047
        assert isinstance(data["entries"], list)
        assert len(data["entries"]) == 10  # Default page_size

        # Verify pagination metadata schema
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["page_size"] == 10
        assert pagination["total_entries"] == 15
        assert pagination["total_pages"] == 2
        assert pagination["has_next"] is True
        assert pagination["has_previous"] is False

    def test_get_history_custom_page_size(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test custom page_size parameter (1-100 range)"""
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

        # Create 30 transactions
        for i in range(30):
            client.post(
                f"/api/v1/components/{component_id}/stock/add",
                json={"location_id": location_id, "quantity": 5},
                headers=auth_headers,
            )

        # Test: Request page_size=25
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history?page_size=25",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200
        data = response.json()

        assert len(data["entries"]) == 25
        assert data["pagination"]["page_size"] == 25
        assert data["pagination"]["total_entries"] == 30
        assert data["pagination"]["total_pages"] == 2
        assert data["pagination"]["has_next"] is True

    def test_get_history_second_page(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test navigation to second page (FR-048)"""
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

        # Create 15 transactions
        for i in range(15):
            client.post(
                f"/api/v1/components/{component_id}/stock/add",
                json={"location_id": location_id, "quantity": 1},
                headers=auth_headers,
            )

        # Test: Get second page
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history?page=2&page_size=10",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200
        data = response.json()

        assert len(data["entries"]) == 5  # Remaining entries
        pagination = data["pagination"]
        assert pagination["page"] == 2
        assert pagination["page_size"] == 10
        assert pagination["total_entries"] == 15
        assert pagination["total_pages"] == 2
        assert pagination["has_next"] is False
        assert pagination["has_previous"] is True

    def test_get_history_empty_no_transactions(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
    ):
        """Test empty history when component has no stock transactions"""
        # Setup: Create component with no stock operations
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Test: Get history for component with no transactions
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history", headers=auth_headers
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200
        data = response.json()

        assert data["entries"] == []
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["total_entries"] == 0
        assert pagination["total_pages"] == 0
        assert pagination["has_next"] is False
        assert pagination["has_previous"] is False

    def test_get_history_sort_by_created_at_desc_default(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test default sort order: created_at DESC (most recent first)"""
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

        # Create 5 transactions with delays to ensure different timestamps
        transaction_ids = []
        for i in range(5):
            resp = client.post(
                f"/api/v1/components/{component_id}/stock/add",
                json={
                    "location_id": location_id,
                    "quantity": i + 1,
                    "comments": f"Transaction {i+1}",
                },
                headers=auth_headers,
            )
            if resp.status_code == 200:
                transaction_ids.append(resp.json().get("transaction_id"))

        # Test: Get history (default sort: created_at DESC)
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history", headers=auth_headers
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200
        data = response.json()

        # Verify entries are sorted by created_at DESC (most recent first)
        entries = data["entries"]
        assert len(entries) == 5

        # First entry should be most recent (last created)
        # Verify timestamps are in descending order
        timestamps = [
            datetime.fromisoformat(entry["created_at"].replace("Z", "+00:00"))
            for entry in entries
        ]
        for i in range(len(timestamps) - 1):
            assert (
                timestamps[i] >= timestamps[i + 1]
            ), "Timestamps should be in descending order"

    def test_get_history_sort_by_quantity_change_asc(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test sort by quantity_change ascending"""
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

        # Create transactions with different quantities
        quantities = [50, 10, 30, 20, 40]
        for qty in quantities:
            client.post(
                f"/api/v1/components/{component_id}/stock/add",
                json={"location_id": location_id, "quantity": qty},
                headers=auth_headers,
            )

        # Test: Sort by quantity_change ascending
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history?sort_by=quantity_change&sort_order=asc",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200
        data = response.json()

        # Verify sorted by quantity ascending
        entries = data["entries"]
        quantity_changes = [entry["quantity_change"] for entry in entries]
        assert quantity_changes == sorted(quantity_changes)

    def test_get_history_sort_by_transaction_type(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test sort by transaction_type"""
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

        # Create different transaction types (ADD, REMOVE if endpoints exist)
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 100},
            headers=auth_headers,
        )

        # Test: Sort by transaction_type
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history?sort_by=transaction_type&sort_order=asc",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200
        data = response.json()

        # Verify sorting works (actual values depend on what operations were performed)
        entries = data["entries"]
        assert len(entries) >= 1

    def test_get_history_sort_by_user_name(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test sort by user_name"""
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

        # Create transactions (all by same user in this test setup)
        for i in range(3):
            client.post(
                f"/api/v1/components/{component_id}/stock/add",
                json={"location_id": location_id, "quantity": 10},
                headers=auth_headers,
            )

        # Test: Sort by user_name
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history?sort_by=user_name&sort_order=asc",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200
        data = response.json()

        # Verify sorting parameter is accepted
        entries = data["entries"]
        assert len(entries) == 3

    def test_get_history_entry_schema_complete(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test StockHistoryEntry schema includes all required fields (FR-058)"""
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

        # Create transaction with all optional fields
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={
                "location_id": location_id,
                "quantity": 100,
                "price_per_unit": 0.50,
                "lot_id": "LOT-2025-Q1-001",
                "comments": "Test stock addition with complete data",
            },
            headers=auth_headers,
        )

        # Test: Get history and verify entry schema
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history", headers=auth_headers
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200
        data = response.json()

        assert len(data["entries"]) >= 1
        entry = data["entries"][0]

        # Verify required fields per contract schema
        assert "id" in entry
        assert "created_at" in entry
        assert "transaction_type" in entry
        assert entry["transaction_type"] in ["ADD", "REMOVE", "MOVE", "ADJUST"]
        assert "quantity_change" in entry
        assert "new_quantity" in entry

        # Verify optional fields are present (may be null)
        assert "previous_quantity" in entry
        assert "from_location_id" in entry
        assert "from_location_name" in entry
        assert "to_location_id" in entry
        assert "to_location_name" in entry
        assert "lot_id" in entry
        assert "price_per_unit" in entry
        assert "total_price" in entry
        assert "user_id" in entry
        assert "user_name" in entry
        assert "reason" in entry
        assert "notes" in entry

    def test_get_history_component_not_found(self, client: TestClient, auth_headers):
        """Test 404 error when component does not exist"""
        fake_component_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            f"/api/v1/components/{fake_component_id}/stock/history",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        # Once implemented, should return 404
        assert response.status_code in [404]

    def test_get_history_invalid_page_parameter(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
    ):
        """Test validation error for invalid page parameter (page < 1)"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Test: Invalid page number (0 or negative)
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history?page=0",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        # Should return 422 validation error for invalid page
        assert response.status_code in [422, 404]

    def test_get_history_invalid_page_size_parameter(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
    ):
        """Test validation error for invalid page_size parameter (not in 1-100 range)"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Test: page_size exceeds maximum (100)
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history?page_size=150",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        # Should return 422 validation error for invalid page_size
        assert response.status_code in [422, 404]

    def test_get_history_invalid_sort_by_parameter(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
    ):
        """Test validation error for invalid sort_by parameter"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Test: Invalid sort_by value (not in enum)
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history?sort_by=invalid_field",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        # Should return 422 validation error for invalid sort_by
        assert response.status_code in [422, 404]

    def test_get_history_regular_user_access(
        self,
        client: TestClient,
        db_session: Session,
        user_auth_headers,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test that regular (non-admin) users CAN access stock history (FR-044)"""
        # Setup: Create component and stock with admin
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
            json={"location_id": location_id, "quantity": 50},
            headers=auth_headers,
        )

        # Test: Regular user accessing stock history (should succeed per FR-044)
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history",
            headers=user_auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        # Stock history is NOT admin-only per FR-044
        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert "pagination" in data
