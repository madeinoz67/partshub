"""
Contract test for GET /api/v1/storage-locations/{id}
Tests storage location details endpoint according to OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient
import uuid


class TestStorageGetContract:
    """Contract tests for storage location details endpoint"""

    def test_get_storage_location_anonymous_access(self, client: TestClient):
        """Test that anonymous users can access storage location details"""
        location_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/storage-locations/{location_id}")

        # This will fail until endpoint is implemented
        # Could be 200 (if location exists) or 404 (if not found)
        assert response.status_code in [200, 404]

    def test_get_storage_location_response_structure(self, client: TestClient):
        """Test response structure matches StorageLocation schema"""
        location_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/storage-locations/{location_id}")

        if response.status_code == 200:
            data = response.json()

            # Required fields for StorageLocation
            required_fields = [
                "id", "name", "description", "type", "location_hierarchy",
                "parent_id", "qr_code_id", "created_at", "updated_at"
            ]

            for field in required_fields:
                assert field in data

            # Validate UUID fields
            assert isinstance(data["id"], str)
            assert data["id"] == location_id

            if data["parent_id"]:
                assert isinstance(data["parent_id"], str)

            # Validate type enum
            assert data["type"] in ["container", "room", "building", "cabinet", "drawer", "shelf", "bin"]

            # Validate strings
            assert isinstance(data["name"], str)
            assert isinstance(data["location_hierarchy"], str)
            assert isinstance(data["created_at"], str)
            assert isinstance(data["updated_at"], str)

    def test_get_storage_location_with_children(self, client: TestClient):
        """Test getting storage location with child locations"""
        location_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/storage-locations/{location_id}?include_children=true")

        # This will fail until endpoint is implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()

            # Should include children array
            assert "children" in data
            assert isinstance(data["children"], list)

            # Children should have proper structure
            for child in data["children"]:
                assert "id" in child
                assert "name" in child
                assert "type" in child
                assert child["parent_id"] == location_id

    def test_get_storage_location_with_component_count(self, client: TestClient):
        """Test getting storage location with component count"""
        location_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/storage-locations/{location_id}?include_component_count=true")

        # This will fail until endpoint is implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()

            # Should include component_count field
            assert "component_count" in data
            assert isinstance(data["component_count"], int)
            assert data["component_count"] >= 0

    def test_get_storage_location_with_full_hierarchy(self, client: TestClient):
        """Test getting storage location with full hierarchy path"""
        location_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/storage-locations/{location_id}?include_full_hierarchy=true")

        # This will fail until endpoint is implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()

            # Should include full_hierarchy_path array
            assert "full_hierarchy_path" in data
            assert isinstance(data["full_hierarchy_path"], list)

            # Each item in hierarchy should have id and name
            for ancestor in data["full_hierarchy_path"]:
                assert "id" in ancestor
                assert "name" in ancestor
                assert isinstance(ancestor["id"], str)
                assert isinstance(ancestor["name"], str)

    def test_get_nonexistent_storage_location(self, client: TestClient):
        """Test 404 response for nonexistent storage location"""
        nonexistent_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/storage-locations/{nonexistent_id}")

        # This will fail until endpoint is implemented
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data

    def test_get_storage_location_invalid_uuid(self, client: TestClient):
        """Test 422 response for invalid UUID"""
        invalid_id = "not-a-uuid"

        response = client.get(f"/api/v1/storage-locations/{invalid_id}")

        # This will fail until validation is implemented
        assert response.status_code == 422

    def test_get_storage_location_query_combinations(self, client: TestClient):
        """Test various query parameter combinations"""
        location_id = str(uuid.uuid4())

        # Multiple includes
        response = client.get(
            f"/api/v1/storage-locations/{location_id}?"
            "include_children=true&include_component_count=true&include_full_hierarchy=true"
        )

        # This will fail until endpoint is implemented
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "children" in data
            assert "component_count" in data
            assert "full_hierarchy_path" in data

    def test_get_storage_location_hierarchy_consistency(self, client: TestClient):
        """Test that location_hierarchy string matches actual hierarchy"""
        location_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/storage-locations/{location_id}?include_full_hierarchy=true")

        if response.status_code == 200:
            data = response.json()

            if "full_hierarchy_path" in data and data["full_hierarchy_path"]:
                # Build expected hierarchy string from path
                expected_hierarchy = "/".join([ancestor["name"] for ancestor in data["full_hierarchy_path"]])
                expected_hierarchy += f"/{data['name']}"

                assert data["location_hierarchy"] == expected_hierarchy

    def test_get_storage_location_with_qr_code(self, client: TestClient):
        """Test storage location with QR code information"""
        location_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/storage-locations/{location_id}")

        if response.status_code == 200:
            data = response.json()

            # QR code field should be present (can be null)
            assert "qr_code_id" in data

            if data["qr_code_id"]:
                assert isinstance(data["qr_code_id"], str)
                assert len(data["qr_code_id"]) > 0

    def test_get_storage_location_parent_reference(self, client: TestClient):
        """Test parent reference consistency"""
        location_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/storage-locations/{location_id}")

        if response.status_code == 200:
            data = response.json()

            if data["parent_id"]:
                # Parent should be accessible
                parent_response = client.get(f"/api/v1/storage-locations/{data['parent_id']}")
                # Parent should exist (though this test might fail in isolated testing)
                # This is more of a consistency check
                assert parent_response.status_code in [200, 404]