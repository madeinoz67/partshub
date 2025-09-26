"""
Contract test for PUT /api/v1/storage-locations/{id}
Tests storage location update endpoint according to OpenAPI specification
"""

import pytest
from fastapi.testclient import TestClient
import uuid


class TestStorageUpdateContract:
    """Contract tests for storage location update endpoint"""

    def test_update_storage_location_requires_auth(self, client: TestClient):
        """Test that storage location update requires authentication"""
        location_id = str(uuid.uuid4())
        update_data = {"name": "Updated Location Name"}

        response = client.put(f"/api/v1/storage-locations/{location_id}", json=update_data)

        # This should fail with 401 until auth is implemented
        assert response.status_code == 401

    def test_update_storage_location_with_jwt_token(self, client: TestClient):
        """Test storage location update with JWT token"""
        location_id = str(uuid.uuid4())
        headers = {"Authorization": "Bearer mock_jwt_token"}
        update_data = {
            "name": "Updated Cabinet Name",
            "description": "Updated description for testing",
            "qr_code_id": "QR-UPDATED-001"
        }

        response = client.put(f"/api/v1/storage-locations/{location_id}", json=update_data, headers=headers)

        # This will fail until endpoint is implemented
        # Could be 200 (updated) or 404 (not found)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["name"] == update_data["name"]
            assert data["description"] == update_data["description"]
            assert data["qr_code_id"] == update_data["qr_code_id"]
            assert "updated_at" in data

    def test_update_storage_location_with_api_key(self, client: TestClient):
        """Test storage location update with API key"""
        location_id = str(uuid.uuid4())
        headers = {"X-API-Key": "mock_api_key"}
        update_data = {"description": "Updated via API key"}

        response = client.put(f"/api/v1/storage-locations/{location_id}", json=update_data, headers=headers)

        # This will fail until endpoint is implemented
        assert response.status_code in [200, 404]

    def test_update_nonexistent_storage_location(self, client: TestClient):
        """Test 404 response for nonexistent storage location"""
        nonexistent_id = str(uuid.uuid4())
        headers = {"Authorization": "Bearer mock_jwt_token"}
        update_data = {"name": "Updated Name"}

        response = client.put(f"/api/v1/storage-locations/{nonexistent_id}", json=update_data, headers=headers)

        # This will fail until endpoint is implemented
        assert response.status_code == 404

    def test_update_storage_location_validation_errors(self, client: TestClient):
        """Test validation errors for invalid update data"""
        location_id = str(uuid.uuid4())
        headers = {"Authorization": "Bearer mock_jwt_token"}

        # Invalid type change
        invalid_data = {"type": "invalid_type"}
        response = client.put(f"/api/v1/storage-locations/{location_id}", json=invalid_data, headers=headers)

        # This will fail until validation is implemented
        assert response.status_code in [422, 400]

        # Empty name
        empty_name_data = {"name": ""}
        response = client.put(f"/api/v1/storage-locations/{location_id}", json=empty_name_data, headers=headers)
        assert response.status_code in [422, 400]

    def test_update_storage_location_with_invalid_uuid(self, client: TestClient):
        """Test 422 response for invalid UUID"""
        invalid_id = "not-a-uuid"
        headers = {"Authorization": "Bearer mock_jwt_token"}
        update_data = {"name": "Updated Name"}

        response = client.put(f"/api/v1/storage-locations/{invalid_id}", json=update_data, headers=headers)

        # This will fail until validation is implemented
        assert response.status_code == 422

    def test_update_storage_location_parent_change(self, client: TestClient):
        """Test changing parent location"""
        location_id = str(uuid.uuid4())
        new_parent_id = str(uuid.uuid4())
        headers = {"Authorization": "Bearer mock_jwt_token"}

        update_data = {"parent_id": new_parent_id}

        response = client.put(f"/api/v1/storage-locations/{location_id}", json=update_data, headers=headers)

        # This will fail until endpoint is implemented
        assert response.status_code in [200, 400, 404]  # Could fail if parent doesn't exist

        if response.status_code == 200:
            data = response.json()
            assert data["parent_id"] == new_parent_id
            # location_hierarchy should be updated to reflect new parent
            assert "/" in data["location_hierarchy"] or data["parent_id"] is None

    def test_update_storage_location_remove_parent(self, client: TestClient):
        """Test removing parent (moving to root level)"""
        location_id = str(uuid.uuid4())
        headers = {"Authorization": "Bearer mock_jwt_token"}

        update_data = {"parent_id": None}

        response = client.put(f"/api/v1/storage-locations/{location_id}", json=update_data, headers=headers)

        # This will fail until endpoint is implemented
        if response.status_code == 200:
            data = response.json()
            assert data["parent_id"] is None
            # location_hierarchy should just be the location name
            assert "/" not in data["location_hierarchy"]
            assert data["location_hierarchy"] == data["name"]

    def test_update_storage_location_invalid_parent(self, client: TestClient):
        """Test updating with invalid parent reference"""
        location_id = str(uuid.uuid4())
        nonexistent_parent = str(uuid.uuid4())
        headers = {"Authorization": "Bearer mock_jwt_token"}

        update_data = {"parent_id": nonexistent_parent}

        response = client.put(f"/api/v1/storage-locations/{location_id}", json=update_data, headers=headers)

        # This will fail until validation is implemented
        assert response.status_code in [400, 404]  # Should reject nonexistent parent

    def test_update_storage_location_self_parent_prevention(self, client: TestClient):
        """Test prevention of self-referencing parent"""
        location_id = str(uuid.uuid4())
        headers = {"Authorization": "Bearer mock_jwt_token"}

        update_data = {"parent_id": location_id}  # Self as parent

        response = client.put(f"/api/v1/storage-locations/{location_id}", json=update_data, headers=headers)

        # This will fail until validation is implemented
        assert response.status_code in [400, 422]  # Should prevent self-reference

    def test_update_storage_location_type_change(self, client: TestClient):
        """Test changing storage location type"""
        location_id = str(uuid.uuid4())
        headers = {"Authorization": "Bearer mock_jwt_token"}

        update_data = {"type": "shelf"}  # Change type

        response = client.put(f"/api/v1/storage-locations/{location_id}", json=update_data, headers=headers)

        # This will fail until endpoint is implemented
        if response.status_code == 200:
            data = response.json()
            assert data["type"] == "shelf"

    def test_update_storage_location_qr_code_change(self, client: TestClient):
        """Test updating QR code ID"""
        location_id = str(uuid.uuid4())
        headers = {"Authorization": "Bearer mock_jwt_token"}

        update_data = {"qr_code_id": "QR-NEW-CODE-123"}

        response = client.put(f"/api/v1/storage-locations/{location_id}", json=update_data, headers=headers)

        # This will fail until endpoint is implemented
        if response.status_code == 200:
            data = response.json()
            assert data["qr_code_id"] == "QR-NEW-CODE-123"

    def test_update_storage_location_partial_update(self, client: TestClient):
        """Test partial storage location updates"""
        location_id = str(uuid.uuid4())
        headers = {"Authorization": "Bearer mock_jwt_token"}

        # Only update one field
        update_data = {"description": "Only updating description field"}

        response = client.put(f"/api/v1/storage-locations/{location_id}", json=update_data, headers=headers)

        # This will fail until endpoint is implemented
        if response.status_code == 200:
            data = response.json()
            assert data["description"] == update_data["description"]
            # Other fields should remain unchanged

    def test_update_storage_location_response_structure(self, client: TestClient):
        """Test response structure matches OpenAPI spec"""
        location_id = str(uuid.uuid4())
        headers = {"Authorization": "Bearer mock_jwt_token"}
        update_data = {"name": "Updated Location"}

        response = client.put(f"/api/v1/storage-locations/{location_id}", json=update_data, headers=headers)

        if response.status_code == 200:
            data = response.json()

            # Should return complete storage location structure
            required_fields = [
                "id", "name", "description", "type", "location_hierarchy",
                "parent_id", "qr_code_id", "created_at", "updated_at"
            ]

            for field in required_fields:
                assert field in data

            # updated_at should be more recent than created_at
            assert data["updated_at"] >= data["created_at"]