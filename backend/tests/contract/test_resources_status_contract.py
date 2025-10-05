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
        # Create test provider, component, provider link, and resource
        from backend.src.models.component import Component
        from backend.src.models.wizard_provider import Provider
        from backend.src.models.provider_link import ProviderLink
        from backend.src.models.resource import Resource

        provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.flush()

        component = Component(name="Test Component")
        db_session.add(component)
        db_session.flush()

        provider_link = ProviderLink(
            component_id=component.id,
            provider_id=provider.id,
            provider_part_number="TEST-STATUS-001",
            provider_url="https://lcsc.com/test",
            sync_status="synced",
        )
        db_session.add(provider_link)
        db_session.flush()

        resource = Resource(
            provider_link_id=provider_link.id,
            resource_type="datasheet",
            file_name="test_datasheet.pdf",
            source_url="https://example.com/datasheet.pdf",
            download_status="pending",
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
        assert data["download_status"] == "pending"
        assert "progress_percent" in data
        assert data["progress_percent"] == 0

    def test_resource_status_downloading(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test resource status during active download"""
        from backend.src.models.component import Component
        from backend.src.models.wizard_provider import Provider
        from backend.src.models.provider_link import ProviderLink
        from backend.src.models.resource import Resource

        provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.flush()

        component = Component(name="Test Component")
        db_session.add(component)
        db_session.flush()

        provider_link = ProviderLink(
            component_id=component.id,
            provider_id=provider.id,
            provider_part_number="TEST-002",
            provider_url="https://lcsc.com/test",
            sync_status="synced",
        )
        db_session.add(provider_link)
        db_session.flush()

        resource = Resource(
            provider_link_id=provider_link.id,
            resource_type="image",
            file_name="component_image.jpg",
            source_url="https://example.com/image.jpg",
            download_status="downloading",
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
        assert data["progress_percent"] == 50  # Service returns 50 for downloading

    def test_resource_status_complete(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test resource status for completed download"""
        from backend.src.models.component import Component
        from backend.src.models.wizard_provider import Provider
        from backend.src.models.provider_link import ProviderLink
        from backend.src.models.resource import Resource

        provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.flush()

        component = Component(name="Test Component")
        db_session.add(component)
        db_session.flush()

        provider_link = ProviderLink(
            component_id=component.id,
            provider_id=provider.id,
            provider_part_number="TEST-003",
            provider_url="https://lcsc.com/test",
            sync_status="synced",
        )
        db_session.add(provider_link)
        db_session.flush()

        resource = Resource(
            provider_link_id=provider_link.id,
            resource_type="datasheet",
            file_name="completed_datasheet.pdf",
            file_path="/resources/datasheets/completed_datasheet.pdf",
            source_url="https://example.com/datasheet.pdf",
            download_status="complete",
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

        assert data["download_status"] == "complete"
        assert data["progress_percent"] == 100
        assert "error_message" not in data or data["error_message"] is None

    def test_resource_status_failed(self, client: TestClient, auth_headers, db_session):
        """Test resource status for failed download"""
        from backend.src.models.component import Component
        from backend.src.models.wizard_provider import Provider
        from backend.src.models.provider_link import ProviderLink
        from backend.src.models.resource import Resource

        provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.flush()

        component = Component(name="Test Component")
        db_session.add(component)
        db_session.flush()

        provider_link = ProviderLink(
            component_id=component.id,
            provider_id=provider.id,
            provider_part_number="TEST-004",
            provider_url="https://lcsc.com/test",
            sync_status="synced",
        )
        db_session.add(provider_link)
        db_session.flush()

        resource = Resource(
            provider_link_id=provider_link.id,
            resource_type="datasheet",
            file_name="failed_datasheet.pdf",
            source_url="https://example.com/datasheet.pdf",
            download_status="failed",
        )
        db_session.add(resource)
        db_session.commit()
        db_session.refresh(resource)

        response = client.get(
            f"/api/resources/{resource.id}/status", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["download_status"] == "failed"
        # Error message format depends on service implementation
        assert "error_message" in data

    def test_resource_status_response_schema(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test response structure matches ResourceStatus schema"""
        from backend.src.models.component import Component
        from backend.src.models.wizard_provider import Provider
        from backend.src.models.provider_link import ProviderLink
        from backend.src.models.resource import Resource

        provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.flush()

        component = Component(name="Test Component")
        db_session.add(component)
        db_session.flush()

        provider_link = ProviderLink(
            component_id=component.id,
            provider_id=provider.id,
            provider_part_number="TEST-005",
            provider_url="https://lcsc.com/test",
            sync_status="synced",
        )
        db_session.add(provider_link)
        db_session.flush()

        resource = Resource(
            provider_link_id=provider_link.id,
            resource_type="datasheet",
            file_name="schema_test.pdf",
            source_url="https://example.com/test.pdf",
            download_status="pending",
        )
        db_session.add(resource)
        db_session.commit()
        db_session.refresh(resource)

        response = client.get(
            f"/api/resources/{resource.id}/status", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Required fields in ResourceStatusResponse schema
        required_fields = [
            "id",
            "download_status",
            "progress_percent",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Optional fields
        assert "error_message" in data
        assert "file_size_bytes" in data
        assert "downloaded_at" in data

    def test_resource_status_multiple_checks(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that status can be checked multiple times"""
        from backend.src.models.component import Component
        from backend.src.models.wizard_provider import Provider
        from backend.src.models.provider_link import ProviderLink
        from backend.src.models.resource import Resource

        provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.flush()

        component = Component(name="Test Component")
        db_session.add(component)
        db_session.flush()

        provider_link = ProviderLink(
            component_id=component.id,
            provider_id=provider.id,
            provider_part_number="TEST-006",
            provider_url="https://lcsc.com/test",
            sync_status="synced",
        )
        db_session.add(provider_link)
        db_session.flush()

        resource = Resource(
            provider_link_id=provider_link.id,
            resource_type="datasheet",
            file_name="multi_check.pdf",
            source_url="https://example.com/test.pdf",
            download_status="downloading",
        )
        db_session.add(resource)
        db_session.commit()
        db_session.refresh(resource)

        # First check
        response1 = client.get(
            f"/api/resources/{resource.id}/status", headers=auth_headers
        )
        assert response1.status_code == 200

        # Second check
        response2 = client.get(
            f"/api/resources/{resource.id}/status", headers=auth_headers
        )
        assert response2.status_code == 200

        # Both should return same ID
        assert response1.json()["id"] == response2.json()["id"]

    def test_resource_status_validation_invalid_id(self, client: TestClient, auth_headers):
        """Test validation error for invalid resource ID"""
        response = client.get("/api/resources/abc/status", headers=auth_headers)

        # Should return 422 validation error
        assert response.status_code == 422
