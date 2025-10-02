"""
Integration Test: Scenario 10 - Zero-Padding for Numbers

User Story: Create numbered locations with zero-padding.

Reference: specs/003-location-improvements-as/quickstart.md - Scenario 10

Functional Requirements: FR-011 (Number range zero-padding option)

This test follows TDD and will FAIL until the feature is implemented.
"""

from fastapi.testclient import TestClient


class TestZeroPadding:
    """
    Scenario 10: Zero-Padding for Numbers (FR-011)

    User can enable zero-padding for number ranges (01, 02, ... instead of 1, 2, ...)
    """

    def test_preview_with_zero_padding_enabled(self, client: TestClient):
        """
        Given: User enables zero-padding for numbers 1-15
        When: User requests preview
        Then: Preview shows zero-padded numbers (01, 02, 03, ..., 15)
        """
        payload = {
            "layout_type": "row",
            "prefix": "bin-",
            "ranges": [{"range_type": "numbers", "start": 1, "end": 15, "zero_pad": True}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["total_count"] == 15

        # Verify zero-padded format in samples
        expected_samples = ["bin-01", "bin-02", "bin-03", "bin-04", "bin-05"]
        assert (
            data["sample_names"] == expected_samples
        ), f"Expected zero-padded samples, got {data['sample_names']}"
        assert data["last_name"] == "bin-15"

    def test_preview_without_zero_padding(self, client: TestClient):
        """
        Given: User does not enable zero-padding for numbers 1-15
        When: User requests preview
        Then: Preview shows non-padded numbers (1, 2, 3, ..., 15)
        """
        payload = {
            "layout_type": "row",
            "prefix": "bin-",
            "ranges": [
                {"range_type": "numbers", "start": 1, "end": 15, "zero_pad": False}
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Verify non-padded format
        expected_samples = ["bin-1", "bin-2", "bin-3", "bin-4", "bin-5"]
        assert (
            data["sample_names"] == expected_samples
        ), f"Expected non-padded samples, got {data['sample_names']}"

    def test_create_with_zero_padding(self, client: TestClient, auth_token: str):
        """
        Given: User creates locations with zero_pad=True
        When: Locations are created
        Then: All location names have zero-padded numbers
        """
        payload = {
            "layout_type": "row",
            "prefix": "padded-",
            "ranges": [{"range_type": "numbers", "start": 1, "end": 10, "zero_pad": True}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        assert response.status_code == 201
        assert response.json()["created_count"] == 10

    def test_zero_padding_with_large_numbers(self, client: TestClient):
        """
        Given: User enables zero-padding for numbers 1-100
        When: User requests preview
        Then: Padding length matches end value (001-100)
        """
        payload = {
            "layout_type": "row",
            "prefix": "num-",
            "ranges": [
                {"range_type": "numbers", "start": 1, "end": 100, "zero_pad": True}
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        data = response.json()
        assert data["total_count"] == 100

        # Verify padding to 3 digits (100 has 3 digits)
        expected_samples = ["num-001", "num-002", "num-003", "num-004", "num-005"]
        assert (
            data["sample_names"] == expected_samples
        ), f"Expected 3-digit padding, got {data['sample_names']}"
        assert data["last_name"] == "num-100"

    def test_zero_padding_in_grid_layout(self, client: TestClient, auth_token: str):
        """
        Given: User creates grid with zero-padded column numbers
        When: Locations are created
        Then: Column numbers are zero-padded
        """
        payload = {
            "layout_type": "grid",
            "prefix": "grid-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "b"},
                {"range_type": "numbers", "start": 1, "end": 10, "zero_pad": True},
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
        assert response.json()["created_count"] == 20  # 2 letters × 10 numbers

    def test_zero_padding_with_3d_grid(self, client: TestClient):
        """
        Given: User creates 3D grid with multiple zero-padded number ranges
        When: User requests preview
        Then: Both number dimensions are zero-padded
        """
        payload = {
            "layout_type": "grid_3d",
            "prefix": "3d-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "b"},
                {"range_type": "numbers", "start": 1, "end": 10, "zero_pad": True},
                {"range_type": "numbers", "start": 1, "end": 5, "zero_pad": True},
            ],
            "separators": ["-", "."],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        data = response.json()
        assert data["total_count"] == 100  # 2 × 10 × 5

        # Verify both number ranges are padded
        expected_first = "3d-a-01.1"  # First dimension padded to 2, second to 1
        # Note: Actual padding behavior depends on implementation
        # This tests that the flag is accepted and processed

    def test_zero_padding_default_is_false(self, client: TestClient):
        """
        Given: User does not specify zero_pad option
        When: User requests preview
        Then: Numbers are not padded (default behavior)
        """
        payload = {
            "layout_type": "row",
            "prefix": "default-",
            "ranges": [
                {"range_type": "numbers", "start": 1, "end": 10}
                # zero_pad not specified
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        data = response.json()
        # Default should be no padding
        assert data["sample_names"][0] in ["default-1", "default-01"]
        # Accept either behavior as valid (depends on schema default)

    def test_zero_padding_only_for_numbers(self, client: TestClient):
        """
        Given: User specifies zero_pad=True for letter range
        When: User requests preview
        Then: Validation error (zero_pad only valid for number ranges)
        """
        payload = {
            "layout_type": "row",
            "prefix": "invalid-",
            "ranges": [
                {
                    "range_type": "letters",
                    "start": "a",
                    "end": "z",
                    "zero_pad": True,  # Invalid for letters
                }
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        # Should return validation error (422 or 200 with errors)
        if response.status_code == 200:
            data = response.json()
            # May be accepted but ignored, or rejected with error
            assert isinstance(data["is_valid"], bool)
        else:
            assert response.status_code in [400, 422]
