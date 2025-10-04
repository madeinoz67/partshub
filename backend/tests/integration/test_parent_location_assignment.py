"""
Integration Test: Scenario 8 - Parent Location Assignment

User Story: Create child locations under a parent.

Reference: specs/003-location-improvements-as/quickstart.md - Scenario 8

Functional Requirements: FR-014 (Parent location assignment)

This test follows TDD and will FAIL until the feature is implemented.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestParentLocationAssignment:
    """
    Scenario 8: Parent Location Assignment (FR-014)

    User can assign generated locations to a parent location in the hierarchy
    """

    def test_create_child_locations_under_parent(
        self, client: TestClient, auth_token: str
    ):
        """
        Given: Parent location 'cabinet-1' exists
        When: User creates child locations 'drawer-a' through 'drawer-d' with parent
        Then: All child locations are created under parent
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Create parent location
        parent_payload = {
            "layout_type": "single",
            "prefix": "cabinet-1",
            "ranges": [],
            "separators": [],
            "location_type": "cabinet",
            "single_part_only": False,
        }

        parent_response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=parent_payload,
            headers=headers,
        )
        assert parent_response.status_code == 201
        parent_id = parent_response.json()["created_ids"][0]

        # Create child locations with parent_id
        child_payload = {
            "layout_type": "row",
            "prefix": "drawer-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "d"}],
            "separators": [],
            "parent_id": parent_id,
            "location_type": "drawer",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=child_payload,
            headers=headers,
        )

        assert response.status_code == 201, "Child locations should be created"
        data = response.json()
        assert data["created_count"] == 4, "Should create 4 child locations"
        assert len(data["created_ids"]) == 4

    def test_reject_nonexistent_parent_id(self, client: TestClient, auth_token: str):
        """
        Given: User specifies non-existent parent_id
        When: User tries to create child locations
        Then: Request is rejected with 400/404 error
        """
        import uuid

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
            "/api/v1/storage-locations/bulk-create-layout",
            json=payload,
            headers=headers,
        )

        # Should reject with 400 Bad Request or 404 Not Found
        assert response.status_code in [
            400,
            404,
        ], f"Expected 400/404 for nonexistent parent, got {response.status_code}"

    def test_create_without_parent_id(self, client: TestClient, auth_token: str):
        """
        Given: User does not specify parent_id
        When: User creates locations
        Then: Locations are created at root level (parent_id = None)
        """
        payload = {
            "layout_type": "row",
            "prefix": "root-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
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
        assert response.json()["created_count"] == 3

    def test_multilevel_hierarchy(self, client: TestClient, auth_token: str):
        """
        Given: 3-level hierarchy (building > room > cabinet)
        When: User creates child locations at each level
        Then: Hierarchy is maintained correctly
        """
        headers = {"Authorization": f"Bearer {auth_token}"}

        # Level 1: Building
        building_payload = {
            "layout_type": "single",
            "prefix": "building-A",
            "ranges": [],
            "separators": [],
            "location_type": "room",  # Using 'room' as building type
            "single_part_only": False,
        }
        building_resp = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=building_payload,
            headers=headers,
        )
        building_id = building_resp.json()["created_ids"][0]

        # Level 2: Rooms under building
        room_payload = {
            "layout_type": "row",
            "prefix": "room-",
            "ranges": [{"range_type": "numbers", "start": 1, "end": 2}],
            "separators": [],
            "parent_id": building_id,
            "location_type": "room",
            "single_part_only": False,
        }
        room_resp = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=room_payload,
            headers=headers,
        )
        assert room_resp.status_code == 201
        room_id = room_resp.json()["created_ids"][0]

        # Level 3: Cabinets under room
        cabinet_payload = {
            "layout_type": "row",
            "prefix": "cabinet-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "parent_id": room_id,
            "location_type": "cabinet",
            "single_part_only": False,
        }
        cabinet_resp = client.post(
            "/api/v1/storage-locations/bulk-create-layout",
            json=cabinet_payload,
            headers=headers,
        )

        assert cabinet_resp.status_code == 201
        assert cabinet_resp.json()["created_count"] == 3

    def test_parent_id_accepts_null(self, client: TestClient, auth_token: str):
        """
        Given: User explicitly sets parent_id to null
        When: User creates locations
        Then: Locations are created at root level
        """
        payload = {
            "layout_type": "row",
            "prefix": "explicit-null-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "a"}],
            "separators": [],
            "parent_id": None,
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

    def test_preview_accepts_parent_id(self, client: TestClient):
        """
        Given: User includes parent_id in preview request
        When: User requests preview
        Then: Preview accepts parent_id (validation happens at creation time)
        """
        import uuid

        parent_id = str(uuid.uuid4())

        payload = {
            "layout_type": "row",
            "prefix": "preview-child-",
            "ranges": [{"range_type": "letters", "start": "a", "end": "c"}],
            "separators": [],
            "parent_id": parent_id,
            "location_type": "bin",
            "single_part_only": False,
        }

        response = client.post(
            "/api/v1/storage-locations/generate-preview", json=payload
        )

        # Preview should accept parent_id without validating existence
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
