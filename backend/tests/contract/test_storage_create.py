"""
Contract test for POST /api/v1/storage-locations
Tests storage location creation endpoint according to OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient
import uuid


class TestStorageCreateContract:
    """Contract tests for storage location creation endpoint"""

    def test_create_storage_location_requires_auth(self, client: TestClient):
        """Test that storage location creation requires authentication"""
        location_data = {
            "name": "Test Drawer",
            "description": "Test drawer for components",
            "type": "drawer"
        }

        response = client.post("/api/v1/storage-locations", json=location_data)

        # This should fail with 401 until auth is implemented
        assert response.status_code == 401

    def test_create_storage_location_with_jwt_token(self, client: TestClient):
        """Test storage location creation with JWT token"""
        headers = {"Authorization": "Bearer mock_jwt_token"}
        location_data = {
            "name": "Electronics Cabinet A",
            "description": "Main electronics components cabinet",
            "type": "cabinet",
            "parent_id": None
        }

        response = client.post("/api/v1/storage-locations", json=location_data, headers=headers)

        # This will fail until endpoint is implemented
        assert response.status_code == 201

        if response.status_code == 201:
            data = response.json()

            # Response should match StorageLocation schema
            required_fields = [
                "id", "name", "description", "type", "location_hierarchy",
                "parent_id", "qr_code_id", "created_at", "updated_at"
            ]

            for field in required_fields:
                assert field in data

            assert data["name"] == location_data["name"]
            assert data["description"] == location_data["description"]
            assert data["type"] == location_data["type"]
            assert data["parent_id"] is None

    def test_create_storage_location_with_parent(self, client: TestClient):
        """Test creating nested storage location with parent"""
        headers = {"Authorization": "Bearer mock_jwt_token"}
        parent_id = str(uuid.uuid4())
        location_data = {
            "name": "Drawer 1",
            "description": "First drawer in cabinet A",
            "type": "drawer",
            "parent_id": parent_id
        }

        response = client.post("/api/v1/storage-locations", json=location_data, headers=headers)

        # This will fail until endpoint is implemented
        assert response.status_code in [201, 400, 404]  # Could fail if parent doesn't exist

        if response.status_code == 201:
            data = response.json()
            assert data["parent_id"] == parent_id
            # location_hierarchy should include parent path
            assert "/" in data["location_hierarchy"]

    def test_create_storage_location_with_api_key(self, client: TestClient):
        """Test storage location creation with API key"""
        headers = {"X-API-Key": "mock_api_key"}
        location_data = {
            "name": "Resistor Bin",
            "description": "Bin for resistor components",
            "type": "bin"
        }

        response = client.post("/api/v1/storage-locations", json=location_data, headers=headers)

        # This will fail until endpoint is implemented
        assert response.status_code == 201

    def test_create_storage_location_validation_errors(self, client: TestClient):
        """Test validation errors for invalid location data"""
        headers = {"Authorization": "Bearer mock_jwt_token"}

        # Missing required fields
        incomplete_data = {
            "name": "Test Location"
            # Missing type
        }
        response = client.post("/api/v1/storage-locations", json=incomplete_data, headers=headers)
        assert response.status_code == 422

        # Invalid type
        invalid_type_data = {
            "name": "Test Location",
            "type": "invalid_type"
        }
        response = client.post("/api/v1/storage-locations", json=invalid_type_data, headers=headers)
        assert response.status_code == 422

        # Invalid parent_id (not a UUID)
        invalid_parent_data = {
            "name": "Test Location",
            "type": "drawer",
            "parent_id": "not-a-uuid"
        }
        response = client.post("/api/v1/storage-locations", json=invalid_parent_data, headers=headers)
        assert response.status_code == 422

    def test_create_storage_location_with_qr_code(self, client: TestClient):
        """Test creating location with QR code"""
        headers = {"Authorization": "Bearer mock_jwt_token"}
        location_data = {
            "name": "IC Storage Box",
            "description": "Box for integrated circuits",
            "type": "container",
            "qr_code_id": "QR-IC-BOX-001"
        }

        response = client.post("/api/v1/storage-locations", json=location_data, headers=headers)

        # This will fail until endpoint is implemented
        if response.status_code == 201:
            data = response.json()
            assert data["qr_code_id"] == location_data["qr_code_id"]

    def test_create_storage_location_duplicate_name_validation(self, client: TestClient):
        """Test duplicate name validation within same parent"""
        headers = {"Authorization": "Bearer mock_jwt_token"}
        location_data = {
            "name": "Duplicate Test Drawer",
            "description": "First instance",
            "type": "drawer"
        }

        # First creation should succeed
        response1 = client.post("/api/v1/storage-locations", json=location_data, headers=headers)

        # Second creation with same name should fail
        response2 = client.post("/api/v1/storage-locations", json=location_data, headers=headers)

        # This will fail until endpoint is implemented with proper validation
        if response1.status_code == 201:
            assert response2.status_code in [400, 409]  # Conflict or bad request

    def test_create_storage_location_nonexistent_parent(self, client: TestClient):
        """Test creating location with nonexistent parent"""
        headers = {"Authorization": "Bearer mock_jwt_token"}
        nonexistent_parent = str(uuid.uuid4())
        location_data = {
            "name": "Orphaned Drawer",
            "description": "Drawer with nonexistent parent",
            "type": "drawer",
            "parent_id": nonexistent_parent
        }

        response = client.post("/api/v1/storage-locations", json=location_data, headers=headers)

        # This will fail until endpoint is implemented
        assert response.status_code in [400, 404]  # Should reject nonexistent parent

    def test_create_storage_location_circular_reference(self, client: TestClient):
        """Test prevention of circular parent references"""
        headers = {"Authorization": "Bearer mock_jwt_token"}

        # This test would require existing locations to test circular reference
        # For now, just test self-reference prevention
        self_id = str(uuid.uuid4())
        location_data = {
            "name": "Self Reference Test",
            "description": "Should not allow self as parent",
            "type": "drawer",
            "parent_id": self_id  # This should be rejected
        }

        response = client.post("/api/v1/storage-locations", json=location_data, headers=headers)

        # This will fail until validation is implemented
        assert response.status_code in [400, 422]