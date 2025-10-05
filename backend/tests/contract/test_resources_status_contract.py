"""
Contract test for GET /api/resources/{resource_id}/status
Tests resource download status endpoint for async resource downloads.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestResourcesStatusContract:
    """Contract tests for resource status endpoint"""

    def test_resource_status_requires_admin_auth(self, client: TestClient):
        """Test that resource status requires admin authentication"""
        response = client.get("/api/resources/1/status")

        # Should fail with 401 unauthorized
        assert response.status_code == 401

    def test_resource_status_non_admin_forbidden(
        self, client: TestClient, user_auth_headers
    ):
        """Test that non-admin users cannot check resource status"""
        response = client.get("/api/resources/1/status", headers=user_auth_headers)

        # Should fail with 403 forbidden
        assert response.status_code == 403

    def test_resource_status_not_found(self, client: TestClient, auth_headers):
        """Test resource status for non-existent resource"""
        response = client.get("/api/resources/99999/status", headers=auth_headers)

        # Should return 404 for non-existent resource
        assert response.status_code == 404

    def test_resource_status_pending(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test resource status for pending download"""
        # Create a test resource with pending status
        # Note: This assumes a Resource model exists
        # This test will fail until Resource model is implemented
        from backend.src.models.resource import Resource

        resource = Resource(
            type="datasheet",
            file_name="test_datasheet.pdf",
            source_url="https://example.com/datasheet.pdf",
            download_status="pending",
            progress_percent=0,
        )
        db_session.add(resource)
        db_session.commit()
        db_session.refresh(resource)

        response = client.get(
            f"/api/resources/{resource.id}/status", headers=auth_headers
        )

        # Debug output if fails
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

        assert response.status_code == 200

        data = response.json()
        assert data["id"] == resource.id
        assert data["download_status"] == "pending"
        assert "progress_percent" in data
        assert data["progress_percent"] == 0

    def test_resource_status_downloading(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test resource status during active download"""
        from backend.src.models.resource import Resource

        resource = Resource(
            type="image",
            file_name="component_image.jpg",
            source_url="https://example.com/image.jpg",
            download_status="downloading",
            progress_percent=45,
        )
        db_session.add(resource)
        db_session.commit()
        db_session.refresh(resource)

        response = client.get(
            f"/api/resources/{resource.id}/status", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == resource.id
        assert data["download_status"] == "downloading"
        assert data["progress_percent"] == 45

    def test_resource_status_complete(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test resource status for completed download"""
        from backend.src.models.resource import Resource

        resource = Resource(
            type="datasheet",
            file_name="completed_datasheet.pdf",
            file_path="/resources/datasheets/completed_datasheet.pdf",
            source_url="https://example.com/datasheet.pdf",
            download_status="complete",
            progress_percent=100,
            file_size_bytes=1024000,
        )
        db_session.add(resource)
        db_session.commit()
        db_session.refresh(resource)

        response = client.get(
            f"/api/resources/{resource.id}/status", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == resource.id
        assert data["download_status"] == "complete"
        assert data["progress_percent"] == 100
        assert "error_message" not in data or data["error_message"] is None

    def test_resource_status_failed(self, client: TestClient, auth_headers, db_session):
        """Test resource status for failed download"""
        from backend.src.models.resource import Resource

        resource = Resource(
            type="datasheet",
            file_name="failed_datasheet.pdf",
            source_url="https://example.com/datasheet.pdf",
            download_status="failed",
            progress_percent=0,
            error_message="Connection timeout",
        )
        db_session.add(resource)
        db_session.commit()
        db_session.refresh(resource)

        response = client.get(
            f"/api/resources/{resource.id}/status", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == resource.id
        assert data["download_status"] == "failed"
        assert "error_message" in data
        assert data["error_message"] == "Connection timeout"

    def test_resource_status_response_schema(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test response structure matches ResourceStatus schema"""
        from backend.src.models.resource import Resource

        resource = Resource(
            type="datasheet",
            file_name="schema_test.pdf",
            source_url="https://example.com/test.pdf",
            download_status="pending",
            progress_percent=0,
        )
        db_session.add(resource)
        db_session.commit()
        db_session.refresh(resource)

        response = client.get(
            f"/api/resources/{resource.id}/status", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields
        required_fields = ["id", "download_status"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Optional fields (may or may not be present)
        # progress_percent should be present for pending/downloading/complete
        # error_message should be present only for failed status
        assert isinstance(data["id"], int)
        assert data["download_status"] in [
            "pending",
            "downloading",
            "complete",
            "failed",
        ]

    def test_resource_status_multiple_checks(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that status can be checked multiple times"""
        from backend.src.models.resource import Resource

        resource = Resource(
            type="datasheet",
            file_name="multi_check.pdf",
            source_url="https://example.com/test.pdf",
            download_status="downloading",
            progress_percent=25,
        )
        db_session.add(resource)
        db_session.commit()
        db_session.refresh(resource)

        # First check
        response1 = client.get(
            f"/api/resources/{resource.id}/status", headers=auth_headers
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["download_status"] == "downloading"
        assert data1["progress_percent"] == 25

        # Update progress
        resource.progress_percent = 75
        db_session.commit()

        # Second check
        response2 = client.get(
            f"/api/resources/{resource.id}/status", headers=auth_headers
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["download_status"] == "downloading"
        assert data2["progress_percent"] == 75

    def test_resource_status_validation_invalid_id(
        self, client: TestClient, auth_headers
    ):
        """Test resource status with invalid ID format"""
        response = client.get("/api/resources/invalid_id/status", headers=auth_headers)

        # Should return 422 validation error for invalid ID format
        assert response.status_code in [404, 422]
