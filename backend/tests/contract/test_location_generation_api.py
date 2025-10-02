"""
Contract tests for Storage Location Layout Generator API.

These tests validate the API contract (request/response schemas, status codes, authentication)
for the location layout generation endpoints. All tests use isolated in-memory SQLite database.

Test Coverage:
- T010: POST /api/v1/storage-locations/generate-preview
- T011: POST /api/v1/storage-locations/bulk-create-layout (with authentication)

Test Categories:
1. Request schema validation (Pydantic models)
2. Response schema validation (status codes, response structure)
3. Authentication requirements
4. Error response formats
5. Business logic validation (limits, duplicates, warnings)
"""

from fastapi.testclient import TestClient


class TestGeneratePreviewContract:
    """Contract tests for POST /api/v1/storage-locations/generate-preview (T010)"""

    def test_preview_accepts_row_layout_schema(self, client: TestClient):
        """T010.1: FR-002 - Preview endpoint accepts row layout configuration"""
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
        data = response.json()

        # Verify response structure and data
        assert "sample_names" in data
        assert "last_name" in data
        assert "total_count" in data
        assert data["total_count"] == 6, "Should generate 6 locations (a-f)"
        assert data["is_valid"] is True

    def test_preview_accepts_grid_layout_schema(self, client: TestClient):
        """T010.2: FR-003 - Preview endpoint accepts grid layout configuration"""
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
        data = response.json()

        # Verify grid calculation (3 letters × 5 numbers = 15 locations)
        assert data["total_count"] == 15, "Should generate 15 locations (3×5)"
        assert data["is_valid"] is True

    def test_preview_accepts_3d_grid_layout_schema(self, client: TestClient):
        """T010.3: FR-004 - Preview endpoint accepts 3D grid layout configuration"""
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
        data = response.json()

        # Verify 3D grid calculation (2 letters × 3 numbers × 2 numbers = 12 locations)
        assert data["total_count"] == 12, "Should generate 12 locations (2×3×2)"
        assert data["is_valid"] is True

    def test_preview_response_has_required_fields(self, client: TestClient):
        """T010.4: FR-005, FR-013 - Preview response contains all required fields with correct types"""
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
        data = response.json()

        # Validate response schema - all required fields present
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

        # Validate sample_names content
        assert len(data["sample_names"]) <= 5, "sample_names should have max 5 items"
        assert data["sample_names"] == [
            "box-a",
            "box-b",
            "box-c",
        ], "Expected specific names"
        assert data["last_name"] == "box-c", "Last name should match last generated"

    def test_preview_returns_422_for_invalid_range_type(self, client: TestClient):
        """T010.5: FR-017, FR-018 - Validation error for invalid range type"""
        payload = {
            "layout_type": "row",
            "prefix": "box-",
            "ranges": [
                {
                    "range_type": "invalid_type",  # Invalid range type
                    "start": "a",
                    "end": "c",
                }
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        # Should reject invalid enum value
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    def test_preview_validates_start_less_than_end_letters(self, client: TestClient):
        """T010.6: FR-019 - Validation error when start > end for letters"""
        payload = {
            "layout_type": "row",
            "prefix": "box-",
            "ranges": [
                {
                    "range_type": "letters",
                    "start": "z",  # Start > end
                    "end": "a",
                }
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        # Should return 422 validation error for invalid range
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Should include error details"

    def test_preview_validates_start_less_than_end_numbers(self, client: TestClient):
        """T010.7: FR-019 - Validation error when start > end for numbers"""
        payload = {
            "layout_type": "row",
            "prefix": "bin-",
            "ranges": [
                {
                    "range_type": "numbers",
                    "start": 99,  # Start > end
                    "end": 1,
                }
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        # Should return 422 validation error
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    def test_preview_enforces_max_500_locations(self, client: TestClient):
        """T010.8: FR-008 - Validation error when total > 500"""
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
        # Total: 26 × 30 = 780 > 500

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        assert response.status_code == 200, "Should return 200 with errors"
        data = response.json()

        # Should be marked as invalid with error message
        assert data["is_valid"] is False, "Expected is_valid=False for 780 locations"
        assert len(data["errors"]) > 0, "Expected validation errors"
        assert any(
            "500" in error for error in data["errors"]
        ), "Expected 500 limit error message"

    def test_preview_shows_warning_above_100_locations(self, client: TestClient):
        """T010.9: FR-009 - Warning when creating > 100 locations (but still valid)"""
        payload = {
            "layout_type": "grid",
            "prefix": "warn-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "f"},  # 6
                {"range_type": "numbers", "start": 1, "end": 20},  # 20
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 6 × 20 = 120 > 100

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        assert response.status_code == 200, "Should return 200 (valid)"
        data = response.json()

        # Should be valid but with warning
        assert data["is_valid"] is True, "Expected valid configuration"
        assert len(data["warnings"]) > 0, "Expected warning for 120 locations"
        assert any(
            "cannot be deleted" in w.lower() or "cannot be undone" in w.lower()
            for w in data["warnings"]
        ), "Expected warning about permanence"

    def test_preview_validates_layout_type_requires_correct_range_count(
        self, client: TestClient
    ):
        """T010.10: Validation - Grid layout must have exactly 2 ranges"""
        payload = {
            "layout_type": "grid",  # Grid requires 2 ranges
            "prefix": "test-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c"}
            ],  # Only 1 range
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        # Should return 422 validation error
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    def test_preview_validates_separator_count_matches_ranges(self, client: TestClient):
        """T010.11: Validation - separators length must be len(ranges) - 1"""
        payload = {
            "layout_type": "grid",
            "prefix": "test-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c"},
                {"range_type": "numbers", "start": 1, "end": 3},
            ],
            "separators": ["-", "."],  # Too many separators (should be 1)
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        # Should return 422 validation error
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"


class TestBulkCreateLayoutContract:
    """Contract tests for POST /api/v1/storage-locations/bulk-create-layout (T011)"""

    def test_bulk_create_requires_authentication(self, client: TestClient):
        """T011.1: FR-024 - Bulk create requires authentication"""
        payload = {
            "layout_type": "row",
            "prefix": "test-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        # Request without auth token
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout", json=payload
        )

        assert (
            response.status_code == 401
        ), f"Expected 401 Unauthorized, got {response.status_code}"

    def test_bulk_create_accepts_authenticated_request(
        self, client: TestClient, auth_headers
    ):
        """T011.2: FR-001 - Authenticated users can create locations via bulk-create-layout"""
        payload = {
            "layout_type": "row",
            "prefix": "auth-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=auth_headers,
        )

        # Should return 201 Created
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        data = response.json()
        assert data["success"] is True, "Operation should succeed"
        assert data["created_count"] == 2, "Should create 2 locations (a, b)"

    def test_bulk_create_response_has_required_fields(
        self, client: TestClient, auth_headers
    ):
        """T011.3: FR-022, FR-023 - Bulk create response schema validation"""
        payload = {
            "layout_type": "row",
            "prefix": "resp-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=auth_headers,
        )
        data = response.json()

        # Validate response schema - all required fields
        assert "created_ids" in data, "Missing created_ids field"
        assert "created_count" in data, "Missing created_count field"
        assert "success" in data, "Missing success field"

        # Validate field types
        assert isinstance(data["created_ids"], list), "created_ids must be list"
        assert isinstance(data["created_count"], int), "created_count must be integer"
        assert isinstance(data["success"], bool), "success must be boolean"

        # Validate values for successful creation
        assert data["created_count"] == 3, "Should create 3 locations"
        assert len(data["created_ids"]) == 3, "Should return 3 IDs"
        assert data["success"] is True, "Should succeed"

    def test_bulk_create_prevents_duplicate_names(
        self, client: TestClient, auth_headers
    ):
        """T011.4: FR-007 - Cannot create locations with existing names"""
        payload = {
            "layout_type": "row",
            "prefix": "dup-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        # First creation should succeed
        response1 = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=auth_headers,
        )
        assert response1.status_code == 201, "First creation should succeed"
        data1 = response1.json()
        assert data1["success"] is True, "First creation should succeed"

        # Second creation with same names should fail (duplicate constraint)
        response2 = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=auth_headers,
        )

        # Should return success=False with error message
        assert response2.status_code == 201, "Returns 201 but with success=False"
        data2 = response2.json()
        assert data2["success"] is False, "Expected success=False for duplicates"
        assert data2["created_count"] == 0, "Expected no locations created"
        assert data2["errors"] is not None, "Should include error messages"

    def test_bulk_create_supports_parent_location(
        self, client: TestClient, auth_headers, db_session
    ):
        """T011.5: FR-014 - Can assign generated locations to parent"""
        from backend.src.models.storage_location import StorageLocation

        # Create parent location directly in database
        parent = StorageLocation(
            name="parent-cabinet",
            description="Parent cabinet",
            type="cabinet",
        )
        db_session.add(parent)
        db_session.commit()
        db_session.refresh(parent)

        # Create child locations with parent_id
        child_payload = {
            "layout_type": "row",
            "prefix": "child-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "parent_id": parent.id,
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=child_payload,
            headers=auth_headers,
        )

        assert response.status_code == 201, "Should accept parent_id"
        data = response.json()
        assert data["success"] is True, "Should succeed with parent"
        assert data["created_count"] == 3, "Should create 3 child locations"

        # Verify children have correct parent
        created_child = (
            db_session.query(StorageLocation)
            .filter(StorageLocation.name == "child-a")
            .first()
        )
        assert created_child is not None, "Child location should exist"
        assert created_child.parent_id == parent.id, "Child should reference parent"

    def test_bulk_create_supports_single_part_only_flag(
        self, client: TestClient, auth_headers, db_session
    ):
        """T011.6: FR-015 - Can mark locations as single-part only (API accepts flag)"""
        from backend.src.models.storage_location import StorageLocation

        payload = {
            "layout_type": "row",
            "prefix": "single-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": True,  # Test that API accepts this flag
        }

        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=auth_headers,
        )

        # API should accept the single_part_only flag without error
        assert response.status_code == 201, "Should accept single_part_only flag"
        data = response.json()
        assert data["success"] is True, "Should succeed"
        assert data["created_count"] == 2, "Should create 2 locations"

        # Verify locations were created
        created_location = (
            db_session.query(StorageLocation)
            .filter(StorageLocation.name == "single-a")
            .first()
        )
        assert created_location is not None, "Location should exist"

        # Verify layout_config was stored (single_part_only field persistence is implementation detail)
        assert created_location.layout_config is not None, "layout_config should exist"

    def test_bulk_create_stores_layout_config_metadata(
        self, client: TestClient, auth_headers, db_session
    ):
        """T011.7: FR-016 - Layout configuration persisted for audit"""
        from backend.src.models.storage_location import StorageLocation

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

        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Verify layout_config is stored in database
        location_id = data["created_ids"][0]
        location = db_session.query(StorageLocation).filter_by(id=location_id).first()

        assert location is not None, "Location should exist"
        assert location.layout_config is not None, "layout_config should be persisted"
        assert isinstance(
            location.layout_config, dict
        ), "layout_config should be dict/JSON"
        assert (
            location.layout_config["layout_type"] == "grid"
        ), "Should store layout_type"
        assert location.layout_config["prefix"] == "audit-", "Should store prefix"

    def test_bulk_create_validation_exceeds_500_limit(
        self, client: TestClient, auth_headers
    ):
        """T011.8: FR-008 - Cannot create more than 500 locations at once"""
        payload = {
            "layout_type": "grid",
            "prefix": "over-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "z"},  # 26
                {"range_type": "numbers", "start": 1, "end": 30},  # 30
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 26 × 30 = 780 > 500

        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=auth_headers,
        )

        # Should return 201 with success=False and error
        assert response.status_code == 201, "Returns 201 with error response"
        data = response.json()
        assert data["success"] is False, "Should fail validation"
        assert data["created_count"] == 0, "Should not create any locations"
        assert data["errors"] is not None, "Should include error messages"
        assert any(
            "500" in str(err) for err in data["errors"]
        ), "Should mention 500 limit"

    def test_bulk_create_invalid_layout_configuration(
        self, client: TestClient, auth_headers
    ):
        """T011.9: Validation - Invalid layout configuration returns 422"""
        payload = {
            "layout_type": "grid",  # Grid requires 2 ranges
            "prefix": "invalid-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c"}
            ],  # Only 1 range
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=auth_headers,
        )

        # Pydantic validation should reject before reaching service
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

    def test_bulk_create_nonexistent_parent_id(self, client: TestClient, auth_headers):
        """T011.10: Validation - Nonexistent parent_id should fail"""
        payload = {
            "layout_type": "row",
            "prefix": "orphan-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "parent_id": "00000000-0000-0000-0000-000000000000",  # Nonexistent UUID
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=auth_headers,
        )

        # Should fail with error (service layer validation)
        assert response.status_code == 201, "Returns 201 with error response"
        data = response.json()
        assert data["success"] is False, "Should fail with nonexistent parent"
        assert data["created_count"] == 0, "Should not create any locations"
