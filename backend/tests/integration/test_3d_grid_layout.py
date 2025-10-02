"""
Integration Test: Scenario 3 - 3D Grid Layout

User Story: Create warehouse locations with aisle-shelf-bin structure.

Reference: specs/003-location-improvements-as/quickstart.md - Scenario 3

Functional Requirements: FR-004 (3D Grid layout support)

This test follows TDD and will FAIL until the feature is implemented.
"""

from fastapi.testclient import TestClient


class Test3DGridLayout:
    """
    Scenario 3: 3D Grid Layout (FR-004)

    User creates 3-dimensional layout with aisles (a-c) × shelves (1-4) × bins (1-3)
    """

    def test_preview_3d_grid_layout(self, client: TestClient):
        """
        Given: User configures 3×4×3 3D grid layout
        When: User requests preview
        Then: Preview shows sample names with two separators, total count 36
        """
        payload = {
            "layout_type": "grid_3d",
            "prefix": "warehouse-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c"},
                {"range_type": "numbers", "start": 1, "end": 4},
                {"range_type": "numbers", "start": 1, "end": 3}
            ],
            "separators": ["-", "."],
            "location_type": "bin",
            "single_part_only": False
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"

        data = response.json()
        assert data["is_valid"] is True, "Configuration should be valid"
        assert data["total_count"] == 36, "Should calculate 3×4×3 = 36 locations"

        # Verify preview format with two separators
        expected_samples = [
            "warehouse-a-1.1",
            "warehouse-a-1.2",
            "warehouse-a-1.3",
            "warehouse-a-2.1",
            "warehouse-a-2.2"
        ]
        assert data["sample_names"] == expected_samples, \
            f"Expected {expected_samples}, got {data['sample_names']}"

        # Verify last name
        assert data["last_name"] == "warehouse-c-4.3", "Last location should be warehouse-c-4.3"

    def test_create_3d_grid_all_36_locations(self, client: TestClient, auth_token: str):
        """
        Given: User is authenticated
        When: User creates 3×4×3 3D grid layout
        Then: All 36 locations are created successfully
        """
        payload = {
            "layout_type": "grid_3d",
            "prefix": "warehouse-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c"},
                {"range_type": "numbers", "start": 1, "end": 4},
                {"range_type": "numbers", "start": 1, "end": 3}
            ],
            "separators": ["-", "."],
            "location_type": "bin",
            "single_part_only": False
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/storage-locations/bulk-create", json=payload, headers=headers)

        assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}"

        data = response.json()
        assert data["success"] is True, "Operation should succeed"
        assert data["created_count"] == 36, "Should create all 36 locations"
        assert len(data["created_ids"]) == 36, "Should return 36 location IDs"

    def test_3d_grid_with_different_separators(self, client: TestClient, auth_token: str):
        """
        Given: User configures 3D grid with custom separators
        When: User creates locations
        Then: Locations use both specified separators
        """
        payload = {
            "layout_type": "grid_3d",
            "prefix": "store",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "b"},
                {"range_type": "numbers", "start": 1, "end": 2},
                {"range_type": "numbers", "start": 1, "end": 2}
            ],
            "separators": ["_", "-"],
            "location_type": "bin",
            "single_part_only": False
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/storage-locations/bulk-create", json=payload, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["created_count"] == 8, "Should create 2×2×2 = 8 locations"

    def test_3d_grid_with_all_letters(self, client: TestClient, auth_token: str):
        """
        Given: User configures 3D grid with three letter ranges
        When: User creates locations
        Then: Grid uses letter×letter×letter format
        """
        payload = {
            "layout_type": "grid_3d",
            "prefix": "abc-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "b"},
                {"range_type": "letters", "start": "x", "end": "y"},
                {"range_type": "letters", "start": "m", "end": "n"}
            ],
            "separators": ["-", "-"],
            "location_type": "bin",
            "single_part_only": False
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post("/api/storage-locations/bulk-create", json=payload, headers=headers)

        assert response.status_code == 201
        data = response.json()
        assert data["created_count"] == 8, "Should create 2×2×2 = 8 locations"

    def test_3d_grid_validates_separator_count(self, client: TestClient):
        """
        Given: User configures 3D grid with wrong separator count
        When: User requests preview
        Then: Validation error is returned
        """
        # 3D Grid requires exactly 2 separators, but providing 1
        payload = {
            "layout_type": "grid_3d",
            "prefix": "invalid-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "b"},
                {"range_type": "numbers", "start": 1, "end": 2},
                {"range_type": "numbers", "start": 1, "end": 2}
            ],
            "separators": ["-"],  # Should have 2 separators
            "location_type": "bin",
            "single_part_only": False
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        # Should return validation error (422 or 200 with errors)
        if response.status_code == 200:
            data = response.json()
            assert data["is_valid"] is False, "Should be invalid configuration"
            assert len(data["errors"]) > 0, "Should have validation errors"
        else:
            assert response.status_code == 422

    def test_3d_grid_large_configuration(self, client: TestClient):
        """
        Given: User configures large 3D grid (10×10×5 = 500 locations)
        When: User requests preview
        Then: Preview shows correct total at max limit
        """
        payload = {
            "layout_type": "grid_3d",
            "prefix": "max-",
            "ranges": [
                {"range_type": "numbers", "start": 1, "end": 10},
                {"range_type": "numbers", "start": 1, "end": 10},
                {"range_type": "numbers", "start": 1, "end": 5}
            ],
            "separators": ["-", "."],
            "location_type": "bin",
            "single_part_only": False
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 500, "Should calculate 10×10×5 = 500"
        assert data["is_valid"] is True, "Should be valid at exactly 500 locations"
        assert len(data["warnings"]) > 0, "Should show warning for 500 locations"
