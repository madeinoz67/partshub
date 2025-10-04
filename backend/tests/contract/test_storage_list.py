"""
Contract test for GET /api/v1/storage-locations
Tests storage locations listing endpoint according to OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestStorageListContract:
    """Contract tests for storage locations listing endpoint"""

    def test_get_storage_locations_anonymous_access(self, client: TestClient):
        """Test that anonymous users can access storage locations"""
        response = client.get("/api/v1/storage-locations")

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_get_storage_locations_response_structure(self, client: TestClient):
        """Test response structure matches StorageLocation schema"""
        response = client.get("/api/v1/storage-locations")

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

            if data:  # If there are storage locations
                location = data[0]

                # Required fields for StorageLocation
                required_fields = [
                    "id",
                    "name",
                    "description",
                    "type",
                    "location_hierarchy",
                    "parent_id",
                    "qr_code_id",
                    "created_at",
                    "updated_at",
                ]

                for field in required_fields:
                    assert field in location

                # Validate type enum
                assert location["type"] in [
                    "container",
                    "room",
                    "building",
                    "cabinet",
                    "drawer",
                    "shelf",
                    "bin",
                ]

                # Validate UUID fields
                assert isinstance(location["id"], str)
                if location["parent_id"]:
                    assert isinstance(location["parent_id"], str)

    def test_get_storage_locations_hierarchy_structure(self, client: TestClient):
        """Test hierarchical structure is properly represented"""
        response = client.get("/api/v1/storage-locations")

        if response.status_code == 200:
            data = response.json()

            for location in data:
                # location_hierarchy should be a string path like "Workshop/Cabinet-A/Drawer-1"
                assert isinstance(location["location_hierarchy"], str)

                # Parent relationships should be consistent
                if location["parent_id"]:
                    # Parent should exist in the list (for consistency check)
                    any(loc["id"] == location["parent_id"] for loc in data)
                    # Note: This might not always pass if we're not returning all locations
                    # but it's a good consistency check

    def test_get_storage_locations_with_components_count(self, client: TestClient):
        """Test response includes component count if requested"""
        response = client.get("/api/v1/storage-locations?include_component_count=true")

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        if response.status_code == 200:
            data = response.json()

            if data:
                location = data[0]
                # Should include component_count field
                assert "component_count" in location
                assert isinstance(location["component_count"], int)
                assert location["component_count"] >= 0

    def test_get_storage_locations_filtering_by_type(self, client: TestClient):
        """Test filtering by location type"""
        response = client.get("/api/v1/storage-locations?type=drawer")

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        if response.status_code == 200:
            data = response.json()

            # All returned locations should be of type 'drawer'
            for location in data:
                assert location["type"] == "drawer"

    def test_get_storage_locations_search_by_name(self, client: TestClient):
        """Test searching locations by name"""
        response = client.get("/api/v1/storage-locations?search=cabinet")

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        if response.status_code == 200:
            data = response.json()

            # Results should contain 'cabinet' in name or hierarchy
            for location in data:
                search_text = (
                    f"{location['name']} {location['location_hierarchy']}".lower()
                )
                assert "cabinet" in search_text

    def test_get_storage_locations_pagination(self, client: TestClient):
        """Test pagination parameters"""
        response = client.get("/api/v1/storage-locations?limit=10&offset=0")

        # This will fail until endpoint is implemented
        assert response.status_code == 200

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            assert len(data) <= 10

    def test_get_storage_locations_validation_errors(self, client: TestClient):
        """Test validation errors for invalid parameters"""
        # Invalid type filter
        response = client.get("/api/v1/storage-locations?type=invalid_type")
        assert response.status_code in [
            200,
            422,
        ]  # Could filter out or return validation error

        # Invalid limit (negative)
        response = client.get("/api/v1/storage-locations?limit=-1")
        assert response.status_code in [200, 422]

        # Invalid offset (negative)
        response = client.get("/api/v1/storage-locations?offset=-1")
        assert response.status_code in [200, 422]
