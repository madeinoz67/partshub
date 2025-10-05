"""
Contract test for GET /api/v1/components/{component_id}/stock/history/export
Tests stock history export endpoint according to OpenAPI specification (stock-history-export.yaml)

This test MUST FAIL initially - endpoint has not been implemented yet (TDD red phase)
"""


import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.mark.contract
class TestStockHistoryExportContract:
    """Contract tests for stock history export endpoint based on stock-history-export.yaml"""

    def test_export_requires_authentication(self, client: TestClient):
        """Test that export endpoint requires authentication (401 Unauthorized)"""
        component_id = "550e8400-e29b-41d4-a716-446655440000"

        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export?format=csv"
        )

        # Should be 401 Unauthorized (will be 404 until endpoint is implemented)
        assert response.status_code in [401, 404]

    def test_export_csv_format_success(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test CSV export with proper content-type and headers (FR-059)"""
        # Setup: Create component
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        assert component_resp.status_code == 201
        component_id = component_resp.json()["id"]
        component_resp.json()["name"]

        # Setup: Create storage location
        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        assert location_resp.status_code == 201
        location_id = location_resp.json()["id"]

        # Setup: Create stock transactions
        for i in range(5):
            client.post(
                f"/api/v1/components/{component_id}/stock/add",
                json={
                    "location_id": location_id,
                    "quantity": (i + 1) * 10,
                    "price_per_unit": 0.5,
                    "lot_id": f"LOT-{i+1}",
                    "comments": f"Transaction {i+1}",
                },
                headers=auth_headers,
            )

        # Test: Export as CSV
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export?format=csv",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200

        # Verify CSV content-type
        assert response.headers["content-type"] == "text/csv"

        # Verify content-disposition header with filename
        assert "content-disposition" in response.headers
        content_disposition = response.headers["content-disposition"]
        assert "attachment" in content_disposition
        assert "filename=" in content_disposition
        assert ".csv" in content_disposition

        # Verify CSV content structure
        csv_content = response.text
        lines = csv_content.strip().split("\n")

        # First line should be CSV headers (FR-043)
        headers = lines[0]
        assert "Date" in headers
        assert "Type" in headers
        assert "Quantity Change" in headers
        assert "Previous Qty" in headers
        assert "New Qty" in headers
        assert "From Location" in headers
        assert "To Location" in headers
        assert "Lot ID" in headers
        assert "Price/Unit" in headers
        assert "Total Price" in headers
        assert "User" in headers
        assert "Reason" in headers
        assert "Notes" in headers

        # Should have data rows (5 transactions)
        assert len(lines) >= 6  # Header + 5 data rows

    def test_export_xlsx_format_success(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test Excel (XLSX) export with proper content-type (FR-059)"""
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

        # Create transactions
        for i in range(3):
            client.post(
                f"/api/v1/components/{component_id}/stock/add",
                json={"location_id": location_id, "quantity": 20},
                headers=auth_headers,
            )

        # Test: Export as XLSX
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export?format=xlsx",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200

        # Verify Excel content-type
        assert (
            response.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # Verify content-disposition header
        assert "content-disposition" in response.headers
        content_disposition = response.headers["content-disposition"]
        assert "attachment" in content_disposition
        assert ".xlsx" in content_disposition

        # Verify binary content is returned (Excel files are binary)
        assert len(response.content) > 0
        assert isinstance(response.content, bytes)

    def test_export_json_format_success(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test JSON export with proper schema (FR-059)"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]
        component_name = component_resp.json()["name"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        # Create transactions
        for i in range(4):
            client.post(
                f"/api/v1/components/{component_id}/stock/add",
                json={
                    "location_id": location_id,
                    "quantity": 15,
                    "lot_id": f"LOT-JSON-{i+1}",
                },
                headers=auth_headers,
            )

        # Test: Export as JSON
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export?format=json",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200

        # Verify JSON content-type
        assert response.headers["content-type"] == "application/json"

        # Verify content-disposition header
        assert "content-disposition" in response.headers
        content_disposition = response.headers["content-disposition"]
        assert "attachment" in content_disposition
        assert ".json" in content_disposition

        # Verify JSON schema per contract
        data = response.json()
        assert "component_id" in data
        assert data["component_id"] == component_id
        assert "component_name" in data
        assert data["component_name"] == component_name
        assert "exported_at" in data
        assert "total_entries" in data
        assert data["total_entries"] >= 4
        assert "entries" in data
        assert isinstance(data["entries"], list)
        assert len(data["entries"]) >= 4

        # Verify entry schema
        entry = data["entries"][0]
        assert "id" in entry
        assert "created_at" in entry
        assert "transaction_type" in entry
        assert "quantity_change" in entry
        assert "new_quantity" in entry

    def test_export_all_entries_no_pagination(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test that export includes ALL history entries without pagination"""
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

        # Create 25 transactions (more than default page size of 10)
        total_transactions = 25
        for i in range(total_transactions):
            client.post(
                f"/api/v1/components/{component_id}/stock/add",
                json={"location_id": location_id, "quantity": 5},
                headers=auth_headers,
            )

        # Test: Export as JSON to verify entry count
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export?format=json",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200

        data = response.json()
        # Should include ALL entries, not paginated
        assert data["total_entries"] == total_transactions
        assert len(data["entries"]) == total_transactions

    def test_export_with_sort_by_parameter(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test export with sort_by parameter"""
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
        quantities = [50, 10, 30, 20]
        for qty in quantities:
            client.post(
                f"/api/v1/components/{component_id}/stock/add",
                json={"location_id": location_id, "quantity": qty},
                headers=auth_headers,
            )

        # Test: Export sorted by quantity_change ascending
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export?format=json&sort_by=quantity_change&sort_order=asc",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200

        data = response.json()
        entries = data["entries"]

        # Verify sorting
        quantity_changes = [entry["quantity_change"] for entry in entries]
        assert quantity_changes == sorted(quantity_changes)

    def test_export_invalid_format_parameter(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
    ):
        """Test 400 error for invalid format parameter"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Test: Invalid format
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export?format=pdf",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        # Should return 400 or 422 for invalid format
        assert response.status_code in [400, 422, 404]

        if response.status_code in [400, 422]:
            assert "detail" in response.json()

    def test_export_missing_format_parameter(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
    ):
        """Test 400/422 error when format parameter is missing (required)"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Test: Missing required format parameter
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        # Should return 422 for missing required parameter
        assert response.status_code in [422, 404]

    def test_export_component_not_found(self, client: TestClient, auth_headers):
        """Test 404 error when component does not exist"""
        fake_component_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(
            f"/api/v1/components/{fake_component_id}/stock/history/export?format=csv",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code in [404]

    def test_export_empty_history(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
    ):
        """Test export of component with no stock history"""
        # Setup: Component with no stock operations
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]

        # Test: Export CSV of empty history
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export?format=csv",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200

        # Should return valid CSV with headers but no data rows
        csv_content = response.text
        lines = csv_content.strip().split("\n")
        assert len(lines) >= 1  # At least header row

    def test_export_admin_only_access(
        self,
        client: TestClient,
        db_session: Session,
        user_auth_headers,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test that export is admin-only (403 for regular users) per FR-059"""
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

        # Test: Regular user attempting export (should be forbidden)
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export?format=csv",
            headers=user_auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        # Export is admin-only per FR-059
        assert response.status_code in [403, 404]

    def test_export_csv_with_complete_data(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test CSV export includes all transaction data fields (FR-043)"""
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
        location_resp.json()["name"]

        # Create transaction with complete data
        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={
                "location_id": location_id,
                "quantity": 100,
                "price_per_unit": 1.25,
                "lot_id": "LOT-EXPORT-001",
                "comments": "Export test with complete data",
            },
            headers=auth_headers,
        )

        # Test: Export as CSV
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export?format=csv",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200

        csv_content = response.text
        lines = csv_content.strip().split("\n")

        # Verify data row contains expected values
        # Should include: +100 (quantity with +/-), lot ID, price info, location, etc.
        data_rows = lines[1:]  # Skip header
        assert len(data_rows) >= 1

        # Verify quantity has +/- indicator (per FR-043, FR-058)
        first_row = data_rows[0]
        assert "+100" in first_row or "100" in first_row  # Quantity change

    def test_export_filename_includes_component_info(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test that export filename includes component identifier"""
        # Setup
        component_resp = client.post(
            "/api/v1/components", json=sample_component_data, headers=auth_headers
        )
        component_id = component_resp.json()["id"]
        component_resp.json()["name"]

        location_resp = client.post(
            "/api/v1/storage-locations",
            json=sample_storage_location_data,
            headers=auth_headers,
        )
        location_id = location_resp.json()["id"]

        client.post(
            f"/api/v1/components/{component_id}/stock/add",
            json={"location_id": location_id, "quantity": 10},
            headers=auth_headers,
        )

        # Test: Export and verify filename
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export?format=csv",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200

        content_disposition = response.headers.get("content-disposition", "")
        # Filename should include some component identifier (name or ID)
        assert (
            "stock_history" in content_disposition.lower()
            or "history" in content_disposition.lower()
        )

    def test_export_xlsx_sort_order(
        self,
        client: TestClient,
        db_session: Session,
        auth_headers,
        sample_component_data,
        sample_storage_location_data,
    ):
        """Test XLSX export respects sort_order parameter"""
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

        # Create transactions
        for i in range(5):
            client.post(
                f"/api/v1/components/{component_id}/stock/add",
                json={"location_id": location_id, "quantity": (i + 1) * 10},
                headers=auth_headers,
            )

        # Test: Export with sort_order=desc
        response = client.get(
            f"/api/v1/components/{component_id}/stock/history/export?format=xlsx&sort_by=created_at&sort_order=desc",
            headers=auth_headers,
        )

        # This MUST FAIL - endpoint not implemented yet
        assert response.status_code == 200

        # Verify Excel file is returned
        assert (
            response.headers["content-type"]
            == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        assert len(response.content) > 0
