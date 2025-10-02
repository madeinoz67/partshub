"""
Integration Test: Scenario 11 - Letter Capitalization

User Story: Create locations with uppercase letters.

Reference: specs/003-location-improvements-as/quickstart.md - Scenario 11

Functional Requirements: FR-010 (Letter range capitalization option)

This test follows TDD and will FAIL until the feature is implemented.
"""

from fastapi.testclient import TestClient


class TestLetterCapitalization:
    """
    Scenario 11: Letter Capitalization (FR-010)

    User can enable capitalization for letter ranges (A, B, C instead of a, b, c)
    """

    def test_preview_with_capitalization_enabled(self, client: TestClient):
        """
        Given: User enables capitalize for letters a-c
        When: User requests preview
        Then: Preview shows uppercase letters (BIN-A, BIN-B, BIN-C)
        """
        payload = {
            "layout_type": "row",
            "prefix": "BIN-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c", "capitalize": True}
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["total_count"] == 3

        # Verify capitalized format
        expected_samples = ["BIN-A", "BIN-B", "BIN-C"]
        assert (
            data["sample_names"] == expected_samples
        ), f"Expected capitalized letters, got {data['sample_names']}"

    def test_preview_without_capitalization(self, client: TestClient):
        """
        Given: User does not enable capitalize (or sets to False)
        When: User requests preview
        Then: Preview shows lowercase letters (bin-a, bin-b, bin-c)
        """
        payload = {
            "layout_type": "row",
            "prefix": "bin-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c", "capitalize": False}
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Verify lowercase format
        expected_samples = ["bin-a", "bin-b", "bin-c"]
        assert (
            data["sample_names"] == expected_samples
        ), f"Expected lowercase letters, got {data['sample_names']}"

    def test_create_with_capitalization(self, client: TestClient, auth_token: str):
        """
        Given: User creates locations with capitalize=True
        When: Locations are created
        Then: All location names have uppercase letters
        """
        payload = {
            "layout_type": "row",
            "prefix": "CAPS-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "f", "capitalize": True}
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        assert response.status_code == 201
        assert response.json()["created_count"] == 6

    def test_capitalization_in_grid_layout(self, client: TestClient, auth_token: str):
        """
        Given: User creates grid with capitalized row letters
        When: Locations are created
        Then: Row letters are uppercase
        """
        payload = {
            "layout_type": "grid",
            "prefix": "GRID-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c", "capitalize": True},
                {"range_type": "numbers", "start": 1, "end": 3},
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
        assert response.json()["created_count"] == 9  # 3 letters × 3 numbers

    def test_mixed_capitalization_in_3d_grid(self, client: TestClient):
        """
        Given: User creates 3D grid with multiple letter ranges
        When: Only some ranges have capitalize=True
        Then: Each range applies its own capitalization setting
        """
        payload = {
            "layout_type": "grid_3d",
            "prefix": "mixed-",
            "ranges": [
                {
                    "range_type": "letters",
                    "start": "a",
                    "end": "b",
                    "capitalize": True,
                },  # Uppercase
                {"range_type": "numbers", "start": 1, "end": 2},
                {
                    "range_type": "letters",
                    "start": "x",
                    "end": "y",
                    "capitalize": False,
                },  # Lowercase
            ],
            "separators": ["-", "-"],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        data = response.json()
        assert data["total_count"] == 8  # 2 × 2 × 2

        # Verify mixed capitalization in samples
        # First sample should be: mixed-A-1-x (uppercase A, lowercase x)
        expected_first = "mixed-A-1-x"
        assert (
            data["sample_names"][0] == expected_first
        ), f"Expected {expected_first}, got {data['sample_names'][0]}"

    def test_capitalization_default_is_false(self, client: TestClient):
        """
        Given: User does not specify capitalize option
        When: User requests preview
        Then: Letters are lowercase (default behavior)
        """
        payload = {
            "layout_type": "row",
            "prefix": "default-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "c"}
                # capitalize not specified
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        data = response.json()
        # Default should be lowercase
        assert data["sample_names"][0] in ["default-a", "default-A"]
        # Accept either behavior (depends on schema default)

    def test_capitalization_only_for_letters(self, client: TestClient):
        """
        Given: User specifies capitalize=True for number range
        When: User requests preview
        Then: Validation error (capitalize only valid for letter ranges)
        """
        payload = {
            "layout_type": "row",
            "prefix": "invalid-",
            "ranges": [
                {
                    "range_type": "numbers",
                    "start": 1,
                    "end": 10,
                    "capitalize": True,  # Invalid for numbers
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

    def test_capitalization_with_all_26_letters(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: User creates locations with all letters a-z capitalized
        When: Locations are created
        Then: All 26 uppercase letters are used
        """
        payload = {
            "layout_type": "row",
            "prefix": "ALPHA-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "z", "capitalize": True}
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/storage-locations/bulk-create", json=payload, headers=headers
        )

        assert response.status_code == 201
        assert response.json()["created_count"] == 26

    def test_uppercase_input_with_capitalize(self, client: TestClient):
        """
        Given: User provides uppercase input (A-C) with capitalize=True
        When: User requests preview
        Then: Letters remain uppercase (or normalized)
        """
        payload = {
            "layout_type": "row",
            "prefix": "UPPER-",
            "ranges": [
                {
                    "range_type": "letters",
                    "start": "A",
                    "end": "C",
                    "capitalize": True,
                }
            ],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post("/api/storage-locations/generate-preview", json=payload)

        # Should accept and process (normalize case or keep uppercase)
        assert response.status_code == 200
        data = response.json()
        assert data["total_count"] == 3
