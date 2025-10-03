"""
Integration Test: Scenario 5 - Maximum Limit Enforcement

User Story: User prevented from creating >500 locations.

Reference: specs/003-location-improvements-as/quickstart.md - Scenario 5

Functional Requirements: FR-008 (Maximum 500 locations limit)

This test follows TDD and will FAIL until the feature is implemented.
"""

from fastapi.testclient import TestClient


class TestMaxLimitEnforcement:
    """
    Scenario 5: Maximum Limit Enforcement (FR-008)

    User is prevented from creating more than 500 locations in a single operation
    """

    def test_preview_rejects_780_locations(self, client: TestClient):
        """
        Given: User configures layout generating 780 locations
        When: User requests preview
        Then: Preview shows is_valid=False with error message
        """
        payload = {
            "layout_type": "grid",
            "prefix": "toolarge-",
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

        # Verify validation fails
        assert data["total_count"] == 780, "Should calculate total as 780"
        assert data["is_valid"] is False, "Configuration should be invalid"

        # Verify error message mentions 500 limit
        assert len(data["errors"]) > 0, "Should have error messages"
        error_text = " ".join(data["errors"]).lower()
        assert "500" in error_text, "Error should mention the 500 location limit"
        assert "780" in error_text or "exceeds" in error_text

    def test_preview_accepts_exactly_500_locations(self, client: TestClient):
        """
        Given: User configures layout generating exactly 500 locations
        When: User requests preview
        Then: Configuration is valid (limit is at 500, not < 500)
        """
        payload = {
            "layout_type": "grid",
            "prefix": "max-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "t"},  # 20
                {"range_type": "numbers", "start": 1, "end": 25},  # 25
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 20 * 25 = 500

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        data = response.json()
        assert data["total_count"] == 500
        assert data["is_valid"] is True, "Should be valid at exactly 500 locations"
        assert len(data["warnings"]) > 0, "Should still show warning for large batch"

    def test_preview_rejects_501_locations(self, client: TestClient):
        """
        Given: User configures layout generating 501 locations
        When: User requests preview
        Then: Configuration is invalid (threshold at 501)
        """
        payload = {
            "layout_type": "row",
            "prefix": "over-",
            "ranges": [{"range_type": "numbers", "start": 1, "end": 501}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        data = response.json()
        assert data["total_count"] == 501
        assert data["is_valid"] is False, "Should be invalid at 501 locations"
        assert len(data["errors"]) > 0

    def test_bulk_create_rejects_exceeding_limit(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: User is authenticated
        When: User tries to create 600 locations
        Then: Request is rejected with 400 or 422 status
        """
        payload = {
            "layout_type": "grid",
            "prefix": "reject-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "x"},  # 24
                {"range_type": "numbers", "start": 1, "end": 25},  # 25
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 24 * 25 = 600 > 500

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        # Should reject with client error status
        assert response.status_code in [
            400,
            422,
        ], f"Expected 400/422, got {response.status_code}"

    def test_bulk_create_accepts_exactly_500(self, client: TestClient, auth_token: str):
        """
        Given: User is authenticated
        When: User creates exactly 500 locations
        Then: Request succeeds
        """
        payload = {
            "layout_type": "grid",
            "prefix": "limit-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "t"},  # 20
                {"range_type": "numbers", "start": 1, "end": 25},  # 25
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 20 * 25 = 500

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 201, "Should accept exactly 500 locations"
        data = response.json()
        assert data["created_count"] == 500

    def test_3d_grid_exceeding_limit(self, client: TestClient):
        """
        Given: User configures 3D grid exceeding 500 locations
        When: User requests preview
        Then: Error is shown
        """
        payload = {
            "layout_type": "grid_3d",
            "prefix": "big3d-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "j"},  # 10
                {"range_type": "numbers", "start": 1, "end": 10},  # 10
                {"range_type": "numbers", "start": 1, "end": 6},  # 6
            ],
            "separators": ["-", "."],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 10 * 10 * 6 = 600 > 500

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        data = response.json()
        assert data["total_count"] == 600
        assert data["is_valid"] is False
        assert any("500" in error for error in data["errors"])
