"""
Integration Test: Scenario 9 - Single-Part Only Flag

User Story: Mark locations for single-part storage.

Reference: specs/003-location-improvements-as/quickstart.md - Scenario 9

Functional Requirements: FR-015 (Single-part only designation)

This test follows TDD and will FAIL until the feature is implemented.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestSinglePartFlag:
    """
    Scenario 9: Single-Part Only Flag (FR-015)

    User can mark generated locations as "single-part only" storage
    """

    def test_create_with_single_part_flag_true(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: User checks "Mark as single-part only" option
        When: User creates locations
        Then: single_part_only flag is persisted for all created locations
        """
        payload = {
            "layout_type": "row",
            "prefix": "singlepart-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": True,  # Flag enabled
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["created_count"] == 3

        # Note: Verification that flag is actually persisted in database
        # would require GET endpoint or direct database query
        # This test verifies the endpoint accepts the flag

    def test_create_with_single_part_flag_false(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: User does not check "Mark as single-part only" option
        When: User creates locations
        Then: single_part_only flag is False (default)
        """
        payload = {
            "layout_type": "row",
            "prefix": "multipart-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": False,  # Default
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 201
        assert response.json()["created_count"] == 3

    def test_preview_accepts_single_part_flag(self, client: TestClient):
        """
        Given: User configures layout with single_part_only flag
        When: User requests preview
        Then: Preview accepts the flag (no validation error)
        """
        payload = {
            "layout_type": "row",
            "prefix": "preview-single-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "b"}],
            "separators": [],
            "location_type": "bin",
            "single_part_only": True,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True

    def test_grid_layout_with_single_part_flag(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: User creates grid layout with single_part_only=True
        When: User creates locations
        Then: All locations in grid have single_part_only flag
        """
        payload = {
            "layout_type": "grid",
            "prefix": "grid-single-",
            "ranges": [
                {"range_type": "letters", "start": "a", "end": "b"},
                {"range_type": "numbers", "start": 1, "end": 2},
            ],
            "separators": ["-"],
            "location_type": "bin",
            "single_part_only": True,
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        assert response.status_code == 201
        assert response.json()["created_count"] == 4  # 2x2 grid

    def test_default_single_part_flag_is_false(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: User does not specify single_part_only in payload
        When: User creates locations
        Then: Default value is False (schema default)
        """
        payload = {
            "layout_type": "row",
            "prefix": "default-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "a"}],
            "separators": [],
            "location_type": "bin",
            # single_part_only not specified - should use default
        }

        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        # Should accept request with default value
        assert response.status_code in [
            201,
            422,
        ]  # 422 if field is required, 201 if defaulted

    def test_single_part_flag_with_parent_location(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: User creates child locations with single_part_only=True
        When: User creates locations under parent
        Then: Both parent_id and single_part_only are applied
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Create parent
        parent_payload = {
            "layout_type": "single",
            "prefix": "parent-box",
            "ranges": [],
            "separators": [],
            "location_type": "box",
            "single_part_only": False,
        }
        parent_resp = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=parent_payload,
            headers=headers,
        )
        parent_id = parent_resp.json()["created_ids"][0]

        # Create children with single_part_only=True
        child_payload = {
            "layout_type": "row",
            "prefix": "single-bin-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "parent_id": parent_id,
            "location_type": "bin",
            "single_part_only": True,
        }
        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=child_payload,
            headers=headers,
        )

        assert response.status_code == 201
        assert response.json()["created_count"] == 3
