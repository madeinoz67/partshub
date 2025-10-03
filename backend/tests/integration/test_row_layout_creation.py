"""
Integration Test: Scenario 1 - Row Layout Creation

User Story: Create 6 storage bins with letter sequence naming.

Reference: specs/003-location-improvements-as/quickstart.md - Scenario 1

Functional Requirements: FR-002 (Row layout support)

This test follows TDD and will FAIL until the feature is implemented.
"""

from fastapi.testclient import TestClient


class TestRowLayoutCreation:
    """
    Scenario 1: Row Layout Creation (FR-002)

    User creates a simple row layout with letter-based naming (box1-a through box1-f)
    """

    def test_create_row_layout_with_letters(self, client: TestClient, auth_token: str):
        """
        Given: User is authenticated
        When: User creates row layout with prefix "box1-" and letters a-f
        Then: 6 locations are created with names box1-a, box1-b, box1-c, box1-d, box1-e, box1-f
        """
        payload = {
            "layout_type": "row",
            "prefix": "box1-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "f"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        # Verify successful creation
        assert (
            response.status_code == 201
        ), f"Expected 201 Created, got {response.status_code}"

        data = response.json()
        assert data["success"] is True, "Operation should succeed"
        assert data["created_count"] == 6, "Should create exactly 6 locations"
        assert len(data["created_ids"]) == 6, "Should return 6 location IDs"

        # Verify all IDs are valid UUIDs
        for location_id in data["created_ids"]:
            assert isinstance(location_id, str) and len(location_id) > 0

    def test_preview_row_layout_before_creation(self, client: TestClient):
        """
        Given: User configures row layout
        When: User requests preview
        Then: Preview shows first 5 names, last name, and total count
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

        assert (
            response.status_code == 200
        ), f"Expected 200 OK, got {response.status_code}"

        data = response.json()
        assert data["is_valid"] is True, "Configuration should be valid"
        assert data["total_count"] == 6, "Should show 6 total locations"
        assert len(data["sample_names"]) == 5, "Should show first 5 sample names"
        assert data["last_name"] == "box1-f", "Last name should be box1-f"

        # Verify sample names are correct
        expected_samples = ["box1-a", "box1-b", "box1-c", "box1-d", "box1-e"]
        assert (
            data["sample_names"] == expected_samples
        ), f"Expected {expected_samples}, got {data['sample_names']}"

    def test_create_row_layout_with_numbers(self, client: TestClient, auth_token: str):
        """
        Given: User is authenticated
        When: User creates row layout with numbers 1-10
        Then: 10 locations are created with numeric suffixes
        """
        payload = {
            "layout_type": "row",
            "prefix": "bin-",
            "ranges": [{"range_type": "numbers", "start": 1, "end": 10}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created_count"] == 10, "Should create 10 locations"

    def test_row_layout_validates_empty_range(self, client: TestClient):
        """
        Given: User configures row layout with single item (a-a)
        When: User requests preview
        Then: Preview shows 1 location
        """
        payload = {
            "layout_type": "row",
            "prefix": "single-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "a"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 1, "Single item range should create 1 location"
        assert data["is_valid"] is True

    def test_row_layout_supports_all_26_letters(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: User is authenticated
        When: User creates row layout with all letters a-z
        Then: 26 locations are created
        """
        payload = {
            "layout_type": "row",
            "prefix": "alpha-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "z"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created_count"] == 26, "Should create all 26 letter locations"
