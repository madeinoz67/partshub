"""
Contract test for POST /api/provider-links/{link_id}/resources
Tests adding resources to existing provider links.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestResourcesAddContract:
    """Contract tests for adding resources to provider links"""

    def test_add_resource_requires_admin_auth(self, client: TestClient):
        """Test that adding resources requires admin authentication"""
        resource_data = {
            "type": "datasheet",
            "url": "https://example.com/datasheet.pdf",
            "file_name": "datasheet.pdf",
        }

        response = client.post("/api/provider-links/1/resources", json=resource_data)

        # Should fail with 401 unauthorized
        assert response.status_code == 401

    def test_add_resource_non_admin_forbidden(
        self, client: TestClient, user_auth_headers
    ):
        """Test that non-admin users cannot add resources"""
        resource_data = {
            "type": "datasheet",
            "url": "https://example.com/datasheet.pdf",
            "file_name": "datasheet.pdf",
        }

        response = client.post(
            "/api/provider-links/1/resources",
            json=resource_data,
            headers=user_auth_headers,
        )

        # Should fail with 403 forbidden
        assert response.status_code == 403

    def test_add_resource_provider_link_not_found(
        self, client: TestClient, auth_headers
    ):
        """Test adding resource to non-existent provider link"""
        resource_data = {
            "type": "datasheet",
            "url": "https://example.com/datasheet.pdf",
            "file_name": "datasheet.pdf",
        }

        response = client.post(
            "/api/provider-links/99999/resources",
            json=resource_data,
            headers=auth_headers,
        )

        # Should return 404 for non-existent provider link
        assert response.status_code == 404

    def test_add_datasheet_resource(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test adding a datasheet resource to provider link"""
        # Create test provider and provider link
        from backend.src.models.provider import ComponentDataProvider
        from backend.src.models.provider_link import ProviderLink
        from backend.src.models.component import Component

        provider = ComponentDataProvider(
            name="LCSC",
            api_endpoint="https://api.lcsc.com",
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
            provider_part_number="TEST-001",
            provider_url="https://lcsc.com/test",
            sync_status="synced",
        )
        db_session.add(provider_link)
        db_session.commit()
        db_session.refresh(provider_link)

        resource_data = {
            "type": "datasheet",
            "url": "https://lcsc.com/datasheet/TEST-001.pdf",
            "file_name": "TEST-001_datasheet.pdf",
        }

        response = client.post(
            f"/api/provider-links/{provider_link.id}/resources",
            json=resource_data,
            headers=auth_headers,
        )

        # Debug output if fails
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

        assert response.status_code == 201

        data = response.json()

        # Verify resource fields
        assert data["type"] == "datasheet"
        assert data["file_name"] == "TEST-001_datasheet.pdf"
        assert data["source_url"] == "https://lcsc.com/datasheet/TEST-001.pdf"
        assert data["download_status"] in ["pending", "downloading", "complete"]
        assert "id" in data
        assert "created_at" in data

    def test_add_image_resource(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test adding an image resource to provider link"""
        from backend.src.models.provider import ComponentDataProvider
        from backend.src.models.provider_link import ProviderLink
        from backend.src.models.component import Component

        provider = ComponentDataProvider(
            name="LCSC",
            api_endpoint="https://api.lcsc.com",
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
        db_session.commit()
        db_session.refresh(provider_link)

        resource_data = {
            "type": "image",
            "url": "https://lcsc.com/images/TEST-002.jpg",
            "file_name": "TEST-002_image.jpg",
        }

        response = client.post(
            f"/api/provider-links/{provider_link.id}/resources",
            json=resource_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        assert data["type"] == "image"
        assert data["file_name"] == "TEST-002_image.jpg"
        assert data["source_url"] == "https://lcsc.com/images/TEST-002.jpg"

    def test_add_resource_validation_missing_type(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test validation error when type is missing"""
        from backend.src.models.provider import ComponentDataProvider
        from backend.src.models.provider_link import ProviderLink
        from backend.src.models.component import Component

        provider = ComponentDataProvider(
            name="LCSC",
            api_endpoint="https://api.lcsc.com",
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
        db_session.commit()
        db_session.refresh(provider_link)

        resource_data = {
            # Missing type field
            "url": "https://example.com/file.pdf",
            "file_name": "file.pdf",
        }

        response = client.post(
            f"/api/provider-links/{provider_link.id}/resources",
            json=resource_data,
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_add_resource_validation_invalid_url(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test validation error for invalid URL"""
        from backend.src.models.provider import ComponentDataProvider
        from backend.src.models.provider_link import ProviderLink
        from backend.src.models.component import Component

        provider = ComponentDataProvider(
            name="LCSC",
            api_endpoint="https://api.lcsc.com",
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
        db_session.commit()
        db_session.refresh(provider_link)

        resource_data = {
            "type": "datasheet",
            "url": "not_a_valid_url",
            "file_name": "file.pdf",
        }

        response = client.post(
            f"/api/provider-links/{provider_link.id}/resources",
            json=resource_data,
            headers=auth_headers,
        )

        # Should return validation error for invalid URL
        assert response.status_code == 422

    def test_add_resource_response_schema(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test response structure matches Resource schema"""
        from backend.src.models.provider import ComponentDataProvider
        from backend.src.models.provider_link import ProviderLink
        from backend.src.models.component import Component

        provider = ComponentDataProvider(
            name="LCSC",
            api_endpoint="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.flush()

        component = Component(name="Schema Test Component")
        db_session.add(component)
        db_session.flush()

        provider_link = ProviderLink(
            component_id=component.id,
            provider_id=provider.id,
            provider_part_number="SCHEMA-001",
            provider_url="https://lcsc.com/test",
            sync_status="synced",
        )
        db_session.add(provider_link)
        db_session.commit()
        db_session.refresh(provider_link)

        resource_data = {
            "type": "datasheet",
            "url": "https://example.com/datasheet.pdf",
            "file_name": "datasheet.pdf",
        }

        response = client.post(
            f"/api/provider-links/{provider_link.id}/resources",
            json=resource_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        # Required fields in Resource schema
        required_fields = [
            "id",
            "type",
            "file_name",
            "source_url",
            "download_status",
            "created_at",
        ]

        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Optional fields
        # file_path - present when download complete
        # file_size_bytes - present when download complete
        # downloaded_at - present when download complete

    def test_add_multiple_resources_same_link(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test adding multiple resources to same provider link"""
        from backend.src.models.provider import ComponentDataProvider
        from backend.src.models.provider_link import ProviderLink
        from backend.src.models.component import Component

        provider = ComponentDataProvider(
            name="LCSC",
            api_endpoint="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.flush()

        component = Component(name="Multi Resource Component")
        db_session.add(component)
        db_session.flush()

        provider_link = ProviderLink(
            component_id=component.id,
            provider_id=provider.id,
            provider_part_number="MULTI-001",
            provider_url="https://lcsc.com/test",
            sync_status="synced",
        )
        db_session.add(provider_link)
        db_session.commit()
        db_session.refresh(provider_link)

        # Add datasheet
        datasheet_data = {
            "type": "datasheet",
            "url": "https://example.com/datasheet.pdf",
            "file_name": "datasheet.pdf",
        }
        response1 = client.post(
            f"/api/provider-links/{provider_link.id}/resources",
            json=datasheet_data,
            headers=auth_headers,
        )
        assert response1.status_code == 201

        # Add image
        image_data = {
            "type": "image",
            "url": "https://example.com/image.jpg",
            "file_name": "image.jpg",
        }
        response2 = client.post(
            f"/api/provider-links/{provider_link.id}/resources",
            json=image_data,
            headers=auth_headers,
        )
        assert response2.status_code == 201

        # Both resources should have different IDs
        assert response1.json()["id"] != response2.json()["id"]
