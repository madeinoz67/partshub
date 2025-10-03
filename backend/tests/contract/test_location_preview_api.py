"""
Contract tests for POST /api/storage-locations/generate-preview

Tests request/response schema validation, status codes, and error handling
according to the OpenAPI specification for the preview endpoint.

These tests follow TDD principles and will FAIL until the endpoint is implemented.

References:
- OpenAPI: specs/003-location-improvements-as/contracts/location-layout-api.yaml
- Data Model: specs/003-location-improvements-as/data-model.md
- Functional Requirements: FR-001 through FR-023
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestGeneratePreviewContract:
    """
    Contract tests for preview endpoint (no authentication required)

    The preview endpoint is idempotent and has no side effects - it only
    validates configuration and returns what would be created.
    """

    def test_preview_endpoint_exists(self, client: TestClient):
        """
        Test that the preview endpoint exists and accepts POST requests

        Expected: 200 OK (not 404 Not Found)
        """
        payload = {
            "layout_type": "row",
            "prefix": "test-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        # Should NOT return 404 (endpoint should exist)
        assert response.status_code != 404, "Preview endpoint should exist"
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_preview_accepts_row_layout_schema(self, client: TestClient):
        """
        FR-002: Preview endpoint accepts row layout configuration

        Row layout: prefix + single range (letters OR numbers)
        """
        payload = {
            "layout_type": "row",
            "prefix": "box1-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "f"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_preview_accepts_grid_layout_schema(self, client: TestClient):
        """
        FR-003: Preview endpoint accepts grid layout configuration

        Grid layout: prefix + 2 ranges + 1 separator
        """
        payload = {
            "layout_type": "grid",
            "prefix": "shelf-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c"},
                {"range_type": "numbers", "start": 1, "end": 5},
            ],
            "separators": ["-"],
            "location_type": "drawer",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_preview_accepts_3d_grid_layout_schema(self, client: TestClient):
        """
        FR-004: Preview endpoint accepts 3D grid layout configuration

        3D Grid layout: prefix + 3 ranges + 2 separators
        """
        payload = {
            "layout_type": "grid_3d",
            "prefix": "warehouse-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "b"},
                {"range_type": "numbers", "start": 1, "end": 3},
                {"range_type": "numbers", "start": 1, "end": 2},
            ],
            "separators": ["-", "."],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_preview_response_has_required_fields(self, client: TestClient):
        """
        FR-005, FR-013: Preview response contains all required fields

        Required fields: sample_names, last_name, total_count, warnings, errors, is_valid
        """
        payload = {
            "layout_type": "row",
            "prefix": "box-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        assert response.status_code == 200

        data = response.json()

        # Validate response schema
        assert "sample_names" in data, "Missing sample_names field"
        assert "last_name" in data, "Missing last_name field"
        assert "total_count" in data, "Missing total_count field"
        assert "warnings" in data, "Missing warnings field"
        assert "errors" in data, "Missing errors field"
        assert "is_valid" in data, "Missing is_valid field"

    def test_preview_response_field_types(self, client: TestClient):
        """
        Validate that response fields have correct data types
        """
        payload = {
            "layout_type": "row",
            "prefix": "type-test-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        data = response.json()

        # Validate field types
        assert isinstance(data["sample_names"], list), "sample_names must be list"
        assert isinstance(data["last_name"], str), "last_name must be string"
        assert isinstance(data["total_count"], int), "total_count must be integer"
        assert isinstance(data["warnings"], list), "warnings must be list"
        assert isinstance(data["errors"], list), "errors must be list"
        assert isinstance(data["is_valid"], bool), "is_valid must be boolean"

    def test_preview_returns_422_for_invalid_layout_type(self, client: TestClient):
        """
        Schema validation: Invalid enum value should return 422 Unprocessable Entity
        """
        payload = {
            "layout_type": "invalid_type",
            "prefix": "box-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        assert (
            response.status_code == 422
        ), f"Expected 422 for invalid enum, got {response.status_code}"

    def test_preview_returns_422_for_invalid_range_type(self, client: TestClient):
        """
        FR-017, FR-018: Validation error for invalid range type
        """
        payload = {
            "layout_type": "row",
            "prefix": "box-",
            "ranges": [{"range_type": "invalid", "start": "a", "end": "c"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        assert (
            response.status_code == 422
        ), f"Expected 422 for invalid range_type, got {response.status_code}"

    def test_preview_returns_422_for_missing_required_fields(self, client: TestClient):
        """
        Schema validation: Missing required fields should return 422
        """
        incomplete_payload = {
            "layout_type": "row",
            "prefix": "box-",
            # Missing ranges, separators, location_type
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=incomplete_payload
        )
        assert (
            response.status_code == 422
        ), f"Expected 422 for missing fields, got {response.status_code}"

    def test_preview_validates_start_less_than_end(self, client: TestClient):
        """
        FR-019: Validation error when start > end

        Should either return 422 (schema validation) or 200 with is_valid=False
        """
        payload = {
            "layout_type": "row",
            "prefix": "box-",
            "ranges": [{"range_type": "letters", "start": "z", "end": "a"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        # Accept either schema validation (422) or business logic validation (200 with errors)
        if response.status_code == 200:
            data = response.json()
            assert (
                data["is_valid"] is False
            ), "Expected is_valid=False for invalid range"
            assert len(data["errors"]) > 0, "Expected validation errors in response"
            assert any(
                "start" in err.lower() and "end" in err.lower()
                for err in data["errors"]
            )
        else:
            assert (
                response.status_code == 422
            ), f"Expected 422 or 200, got {response.status_code}"

    def test_preview_enforces_max_500_locations(self, client: TestClient):
        """
        FR-008: Validation error when total > 500

        Should return 200 with is_valid=False and error message
        """
        payload = {
            "layout_type": "grid",
            "prefix": "big-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "z"},  # 26
                {"range_type": "numbers", "start": 1, "end": 30},  # 30
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 26 * 30 = 780 > 500

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        assert response.status_code == 200

        data = response.json()
        assert data["is_valid"] is False, "Expected is_valid=False for 780 locations"
        assert len(data["errors"]) > 0, "Expected error message"
        assert any(
            "500" in error for error in data["errors"]
        ), "Expected 500 limit mentioned in error"

    def test_preview_shows_warning_above_100_locations(self, client: TestClient):
        """
        FR-009: Warning when creating > 100 locations

        Should still be valid but show warning about undeletable locations
        """
        payload = {
            "layout_type": "grid",
            "prefix": "warn-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "f"},  # 6
                {"range_type": "numbers", "start": 1, "end": 25},  # 25
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 6 * 25 = 150 (> 100 but < 500)

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        assert response.status_code == 200

        data = response.json()
        assert (
            data["is_valid"] is True
        ), "Expected valid configuration (within 500 limit)"
        assert len(data["warnings"]) > 0, "Expected warning for 150 locations"
        assert any(
            "cannot be deleted" in w.lower() or "cannot be undone" in w.lower()
            for w in data["warnings"]
        ), "Expected warning about undeletable locations"

    def test_preview_sample_names_limited_to_5(self, client: TestClient):
        """
        FR-013: Preview shows first 5 names only (for performance)
        """
        payload = {
            "layout_type": "row",
            "prefix": "sample-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "z"}],  # 26 total
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        data = response.json()

        assert (
            len(data["sample_names"]) <= 5
        ), "sample_names should be limited to 5 items"
        assert data["total_count"] == 26, "total_count should reflect actual count"

    def test_preview_accepts_optional_parent_id(self, client: TestClient):
        """
        FR-014: Preview accepts optional parent_id field
        """
        import uuid

        parent_id = str(uuid.uuid4())

        payload = {
            "layout_type": "row",
            "prefix": "child-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "parent_id": parent_id,
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        # Should accept parent_id in schema (validation of existence happens at create time)
        assert response.status_code == 200

    def test_preview_accepts_letter_range_options(self, client: TestClient):
        """
        FR-010: Preview accepts capitalize option for letter ranges
        """
        payload = {
            "layout_type": "row",
            "prefix": "CAP-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c", "capitalize": True}
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        assert response.status_code == 200

    def test_preview_accepts_number_range_options(self, client: TestClient):
        """
        FR-011: Preview accepts zero_pad option for number ranges
        """
        payload = {
            "layout_type": "row",
            "prefix": "num-",
            "ranges": [
                {"range_type": "numbers", "start": 1, "end": 15, "zero_pad": True}
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )
        assert response.status_code == 200

    def test_preview_returns_400_for_malformed_json(self, client: TestClient):
        """
        Error handling: Malformed JSON should return 400 Bad Request
        """
        response = client.post(
            "/api/v1/storage-locations/generate-preview",
            data="invalid json{",
            headers={"Content-Type": "application/json"},
        )

        # Should return 400 (Bad Request) for malformed JSON
        assert response.status_code == 400
