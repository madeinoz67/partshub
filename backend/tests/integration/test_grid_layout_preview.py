"""
Integration Test: Scenario 2 - Grid Layout with Preview

User Story: Create 30 drawer locations in a 6×5 grid pattern.

Reference: specs/003-location-improvements-as/quickstart.md - Scenario 2

Functional Requirements: FR-003 (Grid layout), FR-013 (Preview format)

This test follows TDD and will FAIL until the feature is implemented.
"""

from fastapi.testclient import TestClient


class TestGridLayoutPreview:
    """
    Scenario 2: Grid Layout with Preview (FR-003, FR-013)

    User creates 2D grid layout with row letters (a-f) and column numbers (1-5)
    """

    def test_preview_grid_layout_shows_correct_format(self, client: TestClient):
        """
        Given: User configures 6×5 grid layout
        When: User requests preview
        Then: Preview shows sample names in grid format, total count 30
        """
        payload = {
            "layout_type": "grid",
            "prefix": "drawer-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "f"},
                {"range_type": "numbers", "start": 1, "end": 5},
            ],
            "separators": ["-"],
            "location_type": "drawer",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        assert (
            response.status_code == 200
        ), f"Expected 200 OK, got {response.status_code}"

        data = response.json()
        assert data["is_valid"] is True, "Configuration should be valid"
        assert data["total_count"] == 30, "Should calculate 6 rows × 5 columns = 30"

        # Verify preview format (first 5 samples)
        expected_samples = [
            "drawer-a-1",
            "drawer-a-2",
            "drawer-a-3",
            "drawer-a-4",
            "drawer-a-5",
        ]
        assert (
            data["sample_names"] == expected_samples
        ), f"Expected {expected_samples}, got {data['sample_names']}"

        # Verify last name
        assert data["last_name"] == "drawer-f-5", "Last location should be drawer-f-5"

    def test_create_grid_layout_all_30_locations(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: User is authenticated
        When: User creates 6×5 grid layout
        Then: All 30 locations are created successfully
        """
        payload = {
            "layout_type": "grid",
            "prefix": "drawer-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "f"},
                {"range_type": "numbers", "start": 1, "end": 5},
            ],
            "separators": ["-"],
            "location_type": "drawer",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        assert (
            response.status_code == 201
        ), f"Expected 201 Created, got {response.status_code}"

        data = response.json()
        assert data["success"] is True, "Operation should succeed"
        assert data["created_count"] == 30, "Should create all 30 locations"
        assert len(data["created_ids"]) == 30, "Should return 30 location IDs"

    def test_grid_layout_with_custom_separator(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: User configures grid with custom separator (.)
        When: User creates locations
        Then: Locations use the specified separator
        """
        payload = {
            "layout_type": "grid",
            "prefix": "shelf.",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "b"},
                {"range_type": "numbers", "start": 1, "end": 3},
            ],
            "separators": ["."],
            "location_type": "shelf",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created_count"] == 6, "Should create 2×3 = 6 locations"

    def test_grid_layout_with_number_number_ranges(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: User configures grid with two number ranges
        When: User creates locations
        Then: Grid uses number×number format
        """
        payload = {
            "layout_type": "grid",
            "prefix": "rack-",
            "ranges": [
                {"range_type": "numbers", "start": 1, "end": 4},
                {"range_type": "numbers", "start": 1, "end": 5},
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
        data = response.json()
        assert data["created_count"] == 20, "Should create 4×5 = 20 locations"

    def test_grid_layout_preview_performance(self, client: TestClient):
        """
        Given: User configures large grid (26×19 = 494 locations)
        When: User requests preview
        Then: Preview returns quickly with first 5 samples only
        """
        payload = {
            "layout_type": "grid",
            "prefix": "large-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "z"},  # 26
                {"range_type": "numbers", "start": 1, "end": 19},  # 19
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 494, "Should calculate 26×19 = 494"
        assert (
            len(data["sample_names"]) == 5
        ), "Should return only 5 samples for performance"
        assert data["last_name"] == "large-z-19", "Last location should be large-z-19"

    def test_grid_layout_validates_separator_count(self, client: TestClient):
        """
        Given: User configures grid layout with wrong separator count
        When: User requests preview
        Then: Validation error is returned
        """
        # Grid requires exactly 1 separator, but providing 0
        payload = {
            "layout_type": "grid",
            "prefix": "invalid-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c"},
                {"range_type": "numbers", "start": 1, "end": 5},
            ],
            "separators": [],  # Should have 1 separator
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        # Should return validation error (422 or 200 with errors)
        if response.status_code == 200:
            data = response.json()
            assert data["is_valid"] is False, "Should be invalid configuration"
            assert len(data["errors"]) > 0, "Should have validation errors"
        else:
            assert response.status_code == 422
