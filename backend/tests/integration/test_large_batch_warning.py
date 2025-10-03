"""
Integration Test: Scenario 4 - Large Batch Warning

User Story: User warned when creating 100+ locations.

Reference: specs/003-location-improvements-as/quickstart.md - Scenario 4

Functional Requirements: FR-009 (Warning above 100 locations)

This test follows TDD and will FAIL until the feature is implemented.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestLargeBatchWarning:
    """
    Scenario 4: Large Batch Warning (FR-009)

    User is warned when creating more than 100 locations (but still allowed to proceed)
    """

    def test_preview_shows_warning_for_150_locations(self, client: TestClient):
        """
        Given: User configures layout generating 150 locations
        When: User requests preview
        Then: Warning message is shown about inability to delete locations
        """
        payload = {
            "layout_type": "grid",
            "prefix": "big-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "f"},  # 6
                {"range_type": "numbers", "start": 1, "end": 25},  # 25
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 6 * 25 = 150 locations

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        assert response.status_code == 200
        data = response.json()

        # Verify count and validity
        assert data["total_count"] == 150, "Should calculate 150 total locations"
        assert data["is_valid"] is True, "Should still be valid (within 500 limit)"

        # Verify warning exists
        assert len(data["warnings"]) > 0, "Should have at least one warning"

        # Verify warning message content
        warning_text = " ".join(data["warnings"]).lower()
        assert (
            "cannot be deleted" in warning_text or "cannot be undone" in warning_text
        ), "Warning should mention inability to delete locations"

    def test_no_warning_for_100_locations(self, client: TestClient):
        """
        Given: User configures layout generating exactly 100 locations
        When: User requests preview
        Then: No warning is shown (threshold is > 100, not >= 100)
        """
        payload = {
            "layout_type": "grid",
            "prefix": "exact-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "d"},  # 4
                {"range_type": "numbers", "start": 1, "end": 25},  # 25
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 4 * 25 = 100 locations

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        data = response.json()
        assert data["total_count"] == 100
        assert data["is_valid"] is True
        assert len(data["warnings"]) == 0, "Should have no warnings at exactly 100"

    def test_warning_for_101_locations(self, client: TestClient):
        """
        Given: User configures layout generating 101 locations
        When: User requests preview
        Then: Warning is shown (threshold crossed at 101)
        """
        payload = {
            "layout_type": "row",
            "prefix": "threshold-",
            "ranges": [{"range_type": "numbers", "start": 1, "end": 101}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        data = response.json()
        assert data["total_count"] == 101
        assert len(data["warnings"]) > 0, "Should show warning at 101 locations"

    def test_user_can_create_despite_warning(self, client: TestClient, auth_token: str):
        """
        Given: User has warning in preview
        When: User proceeds with creation
        Then: Locations are created successfully
        """
        payload = {
            "layout_type": "grid",
            "prefix": "proceed-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "e"},  # 5
                {"range_type": "numbers", "start": 1, "end": 25},  # 25
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 5 * 25 = 125 locations

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 201, "Should allow creation despite warning"
        data = response.json()
        assert data["success"] is True
        assert data["created_count"] == 125

    def test_warning_for_near_max_limit(self, client: TestClient):
        """
        Given: User configures layout generating 490 locations (near limit)
        When: User requests preview
        Then: Warning is shown
        """
        payload = {
            "layout_type": "grid",
            "prefix": "near-max-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "z"},  # 26
                {"range_type": "numbers", "start": 1, "end": 19},  # 19
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": False,
        }
        # Total: 26 * 19 = 494 locations

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        data = response.json()
        assert data["total_count"] == 494
        assert data["is_valid"] is True
        assert (
            len(data["warnings"]) > 0
        ), "Should show warning for 494 locations (well above 100)"
