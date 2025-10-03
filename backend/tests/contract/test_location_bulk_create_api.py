"""
Contract tests for POST /api/storage-locations/bulk-create

Tests authentication requirements, request/response schemas, and transactional behavior
according to the OpenAPI specification for the bulk create endpoint.

These tests follow TDD principles and will FAIL until the endpoint is implemented.

References:
- OpenAPI: specs/003-location-improvements-as/contracts/location-layout-api.yaml
- Data Model: specs/003-location-improvements-as/data-model.md
- Functional Requirements: FR-001, FR-007, FR-008, FR-014, FR-015, FR-016, FR-024
"""

import uuid

from fastapi.testclient import TestClient


class TestBulkCreateContract:
    """
    Contract tests for bulk create endpoint (authentication required)

    This endpoint creates storage locations in a single transaction (all-or-nothing).
    """

    def test_bulk_create_endpoint_exists(self, client: TestClient, auth_token: str):
        """
        Test that the bulk create endpoint exists and accepts POST requests

        Expected: 201 Created (not 404 Not Found)
        """
        payload = {
            "layout_type": "row",
            "prefix": "test-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        # Should NOT return 404 (endpoint should exist)
        assert response.status_code != 404, "Bulk create endpoint should exist"
        assert (
            response.status_code == 201
        ), f"Expected 201 Created, got {response.status_code}"

    def test_bulk_create_requires_authentication(self, client: TestClient):
        """
        FR-024: Bulk create requires authentication

        Anonymous users MUST NOT be able to create locations (tiered access control)
        """
        payload = {
            "layout_type": "row",
            "prefix": "test-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        # Request without auth token
        response = client.post("/api/storage-locations/bulk-create", json=payload)

        assert (
            response.status_code == 401
        ), f"Expected 401 Unauthorized without token, got {response.status_code}"

        # Verify error response format
        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"

    def test_bulk_create_rejects_invalid_token(self, client: TestClient):
        """
        Authentication: Invalid JWT token should return 401
        """
        payload = {
            "layout_type": "row",
            "prefix": "test-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": "Bearer invalid_token_12345"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        assert (
            response.status_code == 401
        ), f"Expected 401 for invalid token, got {response.status_code}"

    def test_bulk_create_accepts_authenticated_request(
        self, client: TestClient, auth_token: str
    ):
        """
        FR-001: Authenticated users can create locations
        """
        payload = {
            "layout_type": "row",
            "prefix": "auth-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        assert (
            response.status_code == 201
        ), f"Expected 201 Created, got {response.status_code}"

    def test_bulk_create_response_has_required_fields(
        self, client: TestClient, auth_token: str
    ):
        """
        FR-022, FR-023: Bulk create response schema validation

        Required fields: created_ids, created_count, success
        """
        payload = {
            "layout_type": "row",
            "prefix": "resp-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        assert response.status_code == 201
        data = response.json()

        # Validate response schema
        assert "created_ids" in data, "Missing created_ids field"
        assert "created_count" in data, "Missing created_count field"
        assert "success" in data, "Missing success field"

    def test_bulk_create_response_field_types(
        self, client: TestClient, auth_token: str
    ):
        """
        Validate that response fields have correct data types
        """
        payload = {
            "layout_type": "row",
            "prefix": "types-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        data = response.json()

        # Validate field types
        assert isinstance(data["created_ids"], list), "created_ids must be list"
        assert isinstance(data["created_count"], int), "created_count must be integer"
        assert isinstance(data["success"], bool), "success must be boolean"

        # Validate created_ids are valid UUIDs
        for location_id in data["created_ids"]:
            assert isinstance(location_id, str), "Each created_id must be string"
            # Validate UUID format
            try:
                uuid.UUID(location_id)
            except ValueError:
                raise AssertionError(f"Invalid UUID format: {location_id}")

    def test_bulk_create_count_matches_ids(self, client: TestClient, auth_token: str):
        """
        Business logic: created_count must equal len(created_ids)
        """
        payload = {
            "layout_type": "row",
            "prefix": "count-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "d"}
            ],  # 4 locations
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        data = response.json()
        assert data["created_count"] == len(
            data["created_ids"]
        ), "created_count must match length of created_ids list"
        assert data["created_count"] == 4, "Expected 4 locations created"

    def test_bulk_create_prevents_duplicate_names(
        self, client: TestClient, auth_token: str
    ):
        """
        FR-007: Cannot create locations with existing names

        Transactional: If ANY duplicate exists, NO locations are created (rollback)
        """
        payload = {
            "layout_type": "row",
            "prefix": "dup-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}

        # First creation should succeed
        response1 = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )
        assert response1.status_code == 201, "First creation should succeed"
        assert response1.json()["created_count"] == 2, "Should create 2 locations"

        # Second creation with same names should fail
        response2 = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        # Should return 409 Conflict
        assert (
            response2.status_code == 409
        ), f"Expected 409 Conflict for duplicates, got {response2.status_code}"

        # Should have error information
        data = response2.json()
        if "errors" in data:
            assert len(data["errors"]) > 0, "Should have error messages"
            # Error should mention the duplicate names
            error_text = " ".join(data["errors"]).lower()
            assert "duplicate" in error_text or "already exists" in error_text

    def test_bulk_create_transaction_rollback_on_duplicates(
        self, client: TestClient, auth_token: str
    ):
        """
        FR-007: Transactional behavior - all-or-nothing creation

        If duplicates exist, created_count should be 0 (transaction rolled back)
        """
        # Create initial location
        initial_payload = {
            "layout_type": "single",
            "prefix": "txn-a",
            "ranges": [],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        client.post(
            "/api/storage-locations/bulk-create", json=initial_payload, headers=headers
        )

        # Try to create batch that includes the duplicate
        duplicate_batch_payload = {
            "layout_type": "row",
            "prefix": "txn-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c"}
            ],  # txn-a, txn-b, txn-c
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/storage-locations/bulk-create",
            json=duplicate_batch_payload,
            headers=headers,
        )

        # Should fail with 409
        assert response.status_code == 409

        data = response.json()
        # All-or-nothing: created_count should be 0
        assert (
            data.get("created_count", -1) == 0
        ), "Transaction should be rolled back, no locations created"
        assert data.get("success", True) is False, "Operation should not be successful"

    def test_bulk_create_rejects_exceeding_max_limit(
        self, client: TestClient, auth_token: str
    ):
        """
        FR-008: Cannot create more than 500 locations in single request

        Should return 400 Bad Request (or 422)
        """
        payload = {
            "layout_type": "grid",
            "prefix": "limit-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "z"},  # 26
                {"range_type": "numbers", "start": 1, "end": 30},  # 30
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 26 * 30 = 780 > 500

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        # Should reject with 400 or 422
        assert response.status_code in [
            400,
            422,
        ], f"Expected 400/422 for exceeding limit, got {response.status_code}"

    def test_bulk_create_supports_parent_location(
        self, client: TestClient, auth_token: str
    ):
        """
        FR-014: Can assign generated locations to parent

        All created locations should have the same parent_id
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # First create parent location
        parent_payload = {
            "layout_type": "single",
            "prefix": "parent-cabinet",
            "ranges": [],
            "separators": [],
            "location_type": "cabinet",
            "single_part_only": False,
        }

        parent_response = client.post(
            "/api/storage-locations/bulk-create", json=parent_payload, headers=headers
        )
        assert parent_response.status_code == 201
        parent_id = parent_response.json()["created_ids"][0]

        # Create child locations with parent_id
        child_payload = {
            "layout_type": "row",
            "prefix": "drawer-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "parent_id": parent_id,
            "location_type": "drawer",
            "single_part_only": False,
        }

        response = client.post(
            "/api/storage-locations/bulk-create", json=child_payload, headers=headers
        )

        assert response.status_code == 201, "Should accept parent_id"
        assert response.json()["created_count"] == 3, "Should create 3 child locations"

    def test_bulk_create_rejects_nonexistent_parent(
        self, client: TestClient, auth_token: str
    ):
        """
        FR-014: Should reject parent_id that doesn't exist in database
        """
        nonexistent_parent = str(uuid.uuid4())

        payload = {
            "layout_type": "row",
            "prefix": "orphan-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "parent_id": nonexistent_parent,
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        # Should reject with 400 or 404
        assert response.status_code in [
            400,
            404,
        ], f"Expected 400/404 for nonexistent parent, got {response.status_code}"

    def test_bulk_create_supports_single_part_only_flag(
        self, client: TestClient, auth_token: str
    ):
        """
        FR-015: Can mark locations as single-part only
        """
        payload = {
            "layout_type": "row",
            "prefix": "single-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": True,  # Test this flag
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        assert response.status_code == 201, "Should accept single_part_only flag"
        assert response.json()["success"] is True

    def test_bulk_create_stores_layout_config_metadata(
        self, client: TestClient, auth_token: str
    ):
        """
        FR-016: Layout configuration persisted for audit

        This test verifies the endpoint accepts the configuration.
        Actual persistence will be verified in integration tests.
        """
        payload = {
            "layout_type": "grid",
            "prefix": "audit-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "b"},
                {"range_type": "numbers", "start": 1, "end": 2},
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        assert response.status_code == 201
        assert len(response.json()["created_ids"]) == 4  # 2 letters × 2 numbers

    def test_bulk_create_returns_422_for_invalid_schema(
        self, client: TestClient, auth_token: str
    ):
        """
        Schema validation: Invalid request should return 422
        """
        invalid_payload = {
            "layout_type": "invalid_type",
            "prefix": "test-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=invalid_payload, headers=headers
        )

        assert (
            response.status_code == 422
        ), f"Expected 422 for invalid schema, got {response.status_code}"

    def test_bulk_create_returns_422_for_missing_required_fields(
        self, client: TestClient, auth_token: str
    ):
        """
        Schema validation: Missing required fields should return 422
        """
        incomplete_payload = {
            "layout_type": "row",
            "prefix": "test-",
            # Missing ranges, separators, location_type
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create",
            json=incomplete_payload,
            headers=headers,
        )

        assert (
            response.status_code == 422
        ), f"Expected 422 for missing fields, got {response.status_code}"

    def test_bulk_create_supports_all_location_types(
        self, client: TestClient, auth_token: str
    ):
        """
        FR-021: Should accept all valid location types (bin, drawer, shelf, cabinet, room, building)
        """
        location_types = ["bin", "drawer", "shelf", "box", "cabinet", "room"]

        headers = {"Authorization": f"Bearer {auth_token}"}

        for loc_type in location_types:
            payload = {
                "layout_type": "row",
                "prefix": f"{loc_type}-",
                "ranges": [{"range_type": "letters", "start": "a", "end": "a"}],
                "separators": [],
                "location_type": loc_type,
                "single_part_only": False,
            }

            response = client.post(
                "/api/storage-locations/bulk-create", json=payload, headers=headers
            )
            assert (
                response.status_code == 201
            ), f"Should accept location_type '{loc_type}', got {response.status_code}"
