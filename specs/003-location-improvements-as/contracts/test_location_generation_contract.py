"""
Contract tests for Storage Location Layout Generator API.

These tests validate the API contract (request/response schemas, status codes)
before implementation. All tests should FAIL initially (TDD).

Test Categories:
1. Request schema validation (Pydantic models)
2. Response schema validation (status codes, response structure)
3. Authentication requirements
4. Error response formats
"""

import pytest
from fastapi.testclient import TestClient
from typing import Dict, Any


# These tests will fail until the endpoints are implemented
class TestGeneratePreviewContract:
    """Contract tests for POST /api/storage-locations/generate-preview"""

    def test_preview_accepts_row_layout_schema(self, client: TestClient):
        """FR-002: Preview endpoint accepts row layout configuration"""
        payload = {
            "layout_type": "row",
            "prefix": "box1-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "f"}
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        # Should return 200 OK (endpoint exists and accepts schema)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_preview_accepts_grid_layout_schema(self, client: TestClient):
        """FR-003: Preview endpoint accepts grid layout configuration"""
        payload = {
            "layout_type": "grid",
            "prefix": "shelf-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c"},
                {"range_type": "numbers", "start": 1, "end": 5}
            ],
            "separators": ["-"],
            "location_type": "drawer",
            "single_part_only": False
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)
        assert response.status_code == 200

    def test_preview_accepts_3d_grid_layout_schema(self, client: TestClient):
        """FR-004: Preview endpoint accepts 3D grid layout configuration"""
        payload = {
            "layout_type": "grid_3d",
            "prefix": "warehouse-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "b"},
                {"range_type": "numbers", "start": 1, "end": 3},
                {"range_type": "numbers", "start": 1, "end": 2}
            ],
            "separators": ["-", "."],
            "location_type": "bin",
            "single_part_only": False
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)
        assert response.status_code == 200

    def test_preview_response_has_required_fields(self, client: TestClient):
        """FR-005, FR-013: Preview response contains required fields"""
        payload = {
            "layout_type": "row",
            "prefix": "box-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)
        data = response.json()

        # Validate response schema
        assert "sample_names" in data, "Missing sample_names field"
        assert "last_name" in data, "Missing last_name field"
        assert "total_count" in data, "Missing total_count field"
        assert "warnings" in data, "Missing warnings field"
        assert "errors" in data, "Missing errors field"
        assert "is_valid" in data, "Missing is_valid field"

        # Validate field types
        assert isinstance(data["sample_names"], list), "sample_names must be list"
        assert isinstance(data["last_name"], str), "last_name must be string"
        assert isinstance(data["total_count"], int), "total_count must be integer"
        assert isinstance(data["warnings"], list), "warnings must be list"
        assert isinstance(data["errors"], list), "errors must be list"
        assert isinstance(data["is_valid"], bool), "is_valid must be boolean"

    def test_preview_returns_422_for_invalid_range_type(self, client: TestClient):
        """FR-017, FR-018: Validation error for invalid range type"""
        payload = {
            "layout_type": "row",
            "prefix": "box-",
            "ranges": [{"range_type": "invalid", "start": "a", "end": "c"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    def test_preview_validates_start_less_than_end(self, client: TestClient):
        """FR-019: Validation error when start > end"""
        payload = {
            "layout_type": "row",
            "prefix": "box-",
            "ranges": [{"range_type": "letters", "start": "z", "end": "a"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)
        data = response.json()

        # Should either return 422 or 200 with errors in response
        if response.status_code == 200:
            assert data["is_valid"] is False, "Expected is_valid=False for invalid range"
            assert len(data["errors"]) > 0, "Expected validation errors"
        else:
            assert response.status_code == 422

    def test_preview_enforces_max_500_locations(self, client: TestClient):
        """FR-008: Validation error when total > 500"""
        payload = {
            "layout_type": "grid",
            "prefix": "big-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "z"},  # 26
                {"range_type": "numbers", "start": 1, "end": 30}      # 30
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False
        }
        # Total: 26 * 30 = 780 > 500

        response = client.post("/api/storage-locations/generate-preview", json=payload)
        data = response.json()

        assert data["is_valid"] is False, "Expected is_valid=False for 780 locations"
        assert any("500" in error for error in data["errors"]), "Expected 500 limit error"

    def test_preview_shows_warning_above_100_locations(self, client: TestClient):
        """FR-009: Warning when creating > 100 locations"""
        payload = {
            "layout_type": "grid",
            "prefix": "warn-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "f"},  # 6
                {"range_type": "numbers", "start": 1, "end": 20}     # 20
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False
        }
        # Total: 6 * 20 = 120 > 100

        response = client.post("/api/storage-locations/generate-preview", json=payload)
        data = response.json()

        assert data["is_valid"] is True, "Expected valid configuration"
        assert len(data["warnings"]) > 0, "Expected warning for 120 locations"
        assert any("cannot be deleted" in w.lower() for w in data["warnings"])


class TestBulkCreateContract:
    """Contract tests for POST /api/storage-locations/bulk-create"""

    def test_bulk_create_requires_authentication(self, client: TestClient):
        """FR-024: Bulk create requires authentication"""
        payload = {
            "layout_type": "row",
            "prefix": "test-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False
        }

        # Request without auth token
        response = client.post("/api/storage-locations/bulk-create", json=payload)

        assert response.status_code == 401, f"Expected 401 Unauthorized, got {response.status_code}"

    def test_bulk_create_accepts_authenticated_request(self, client: TestClient, auth_token: str):
        """FR-001: Authenticated users can create locations"""
        payload = {
            "layout_type": "row",
            "prefix": "auth-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/storage-locations/bulk-create", json=payload, headers=headers)

        # Should return 201 Created (not 401)
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"

    def test_bulk_create_response_has_required_fields(self, client: TestClient, auth_token: str):
        """FR-022, FR-023: Bulk create response schema validation"""
        payload = {
            "layout_type": "row",
            "prefix": "resp-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/storage-locations/bulk-create", json=payload, headers=headers)
        data = response.json()

        # Validate response schema
        assert "created_ids" in data, "Missing created_ids field"
        assert "created_count" in data, "Missing created_count field"
        assert "success" in data, "Missing success field"

        # Validate field types
        assert isinstance(data["created_ids"], list), "created_ids must be list"
        assert isinstance(data["created_count"], int), "created_count must be integer"
        assert isinstance(data["success"], bool), "success must be boolean"

    def test_bulk_create_prevents_duplicate_names(self, client: TestClient, auth_token: str):
        """FR-007: Cannot create locations with existing names"""
        payload = {
            "layout_type": "row",
            "prefix": "dup-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False
        }

        headers = {"Authorization": f"Bearer {auth_token}"}

        # First creation should succeed
        response1 = client.post("/api/storage-locations/bulk-create", json=payload, headers=headers)
        assert response1.status_code == 201

        # Second creation with same names should fail
        response2 = client.post("/api/storage-locations/bulk-create", json=payload, headers=headers)

        # Should return 409 Conflict or 200 with success=False
        if response2.status_code == 200:
            data = response2.json()
            assert data["success"] is False, "Expected success=False for duplicates"
            assert data["created_count"] == 0, "Expected no locations created"
        else:
            assert response2.status_code == 409, f"Expected 409 Conflict, got {response2.status_code}"

    def test_bulk_create_supports_parent_location(self, client: TestClient, auth_token: str):
        """FR-014: Can assign generated locations to parent"""
        # First create parent location
        parent_payload = {
            "layout_type": "single",
            "prefix": "parent-box",
            "ranges": [],
            "separators": [],
            "location_type": "box",
            "single_part_only": False
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        parent_response = client.post("/api/storage-locations/bulk-create",
                                      json=parent_payload, headers=headers)
        parent_id = parent_response.json()["created_ids"][0]

        # Create child locations with parent_id
        child_payload = {
            "layout_type": "row",
            "prefix": "child-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "parent_id": parent_id,
            "location_type": "bin",
            "single_part_only": False
        }

        response = client.post("/api/storage-locations/bulk-create",
                              json=child_payload, headers=headers)

        assert response.status_code == 201, "Should accept parent_id"

    def test_bulk_create_supports_single_part_only_flag(self, client: TestClient, auth_token: str):
        """FR-015: Can mark locations as single-part only"""
        payload = {
            "layout_type": "row",
            "prefix": "single-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": True  # Test this flag
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/storage-locations/bulk-create", json=payload, headers=headers)

        assert response.status_code == 201, "Should accept single_part_only flag"

    def test_bulk_create_stores_layout_config_metadata(self, client: TestClient, auth_token: str):
        """FR-016: Layout configuration persisted for audit"""
        payload = {
            "layout_type": "grid",
            "prefix": "audit-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "b"},
                {"range_type": "numbers", "start": 1, "end": 2}
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/storage-locations/bulk-create", json=payload, headers=headers)

        assert response.status_code == 201

        # Verify layout_config is stored (will test via GET endpoint or direct DB query)
        location_id = response.json()["created_ids"][0]

        # TODO: Add assertion to verify layout_config field exists in database
        # This will require either:
        # 1. GET /api/storage-locations/{id} endpoint to return layout_config
        # 2. Direct database query in test
        assert location_id is not None, "Location should be created with ID"


# Fixtures (will be implemented in conftest.py)
@pytest.fixture
def client() -> TestClient:
    """FastAPI test client (to be implemented)"""
    # This will fail until the FastAPI app is implemented
    raise NotImplementedError("FastAPI app not implemented yet")


@pytest.fixture
def auth_token() -> str:
    """JWT authentication token for test user (to be implemented)"""
    # This will fail until auth system is implemented
    raise NotImplementedError("Auth system not implemented yet")
