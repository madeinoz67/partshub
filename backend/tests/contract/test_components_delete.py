"""
Contract test for DELETE /api/v1/components/{id}
Tests component deletion endpoint according to OpenAPI specification
"""

import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestComponentsDeleteContract:
    """Contract tests for component deletion endpoint"""

    def test_delete_component_requires_auth(self, client: TestClient):
        """Test that component deletion requires authentication"""
        component_id = str(uuid.uuid4())

        response = client.delete(f"/api/v1/components/{component_id}")

        # This should fail with 401 until auth is implemented
        assert response.status_code == 401

    def test_delete_component_with_jwt_token(self, client: TestClient, auth_headers):
        """Test component deletion with JWT token"""
        component_id = str(uuid.uuid4())

        response = client.delete(
            f"/api/v1/components/{component_id}", headers=auth_headers
        )

        # This will fail until endpoint is implemented
        # Could be 204 (deleted) or 404 (not found)
        assert response.status_code in [204, 404]

        if response.status_code == 204:
            # 204 No Content should have empty response body
            assert response.text == ""

    def test_delete_component_with_api_key(self, client: TestClient, api_token_headers):
        """Test component deletion with API key"""
        component_id = str(uuid.uuid4())

        response = client.delete(
            f"/api/v1/components/{component_id}", headers=api_token_headers
        )

        # This will fail until endpoint is implemented
        assert response.status_code in [204, 404]

    def test_delete_nonexistent_component(self, client: TestClient, auth_headers):
        """Test 404 response for nonexistent component"""
        nonexistent_id = str(uuid.uuid4())

        response = client.delete(
            f"/api/v1/components/{nonexistent_id}", headers=auth_headers
        )

        # This will fail until endpoint is implemented
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data

    def test_delete_component_with_invalid_uuid(self, client: TestClient, auth_headers):
        """Test 422 response for invalid UUID"""
        invalid_id = "not-a-uuid"

        response = client.delete(
            f"/api/v1/components/{invalid_id}", headers=auth_headers
        )

        # This will fail until validation is implemented
        assert response.status_code == 422

    def test_delete_component_cascade_behavior(self, client: TestClient, auth_headers):
        """Test that component deletion handles related data correctly"""
        component_id = str(uuid.uuid4())

        response = client.delete(
            f"/api/v1/components/{component_id}", headers=auth_headers
        )

        # This will fail until endpoint is implemented
        # Should succeed even if component has related stock transactions, etc.
        # (depending on cascade rules defined in data model)
        assert response.status_code in [204, 404, 409]

        # If 409 Conflict, should indicate why deletion failed
        if response.status_code == 409:
            data = response.json()
            assert "detail" in data

    def test_delete_component_idempotency(self, client: TestClient, auth_headers):
        """Test that deleting same component twice returns 404"""
        component_id = str(uuid.uuid4())

        # First deletion
        client.delete(f"/api/v1/components/{component_id}", headers=auth_headers)

        # Second deletion of same component
        response2 = client.delete(
            f"/api/v1/components/{component_id}", headers=auth_headers
        )

        # This will fail until endpoint is implemented
        # Second delete should return 404
        assert response2.status_code == 404
