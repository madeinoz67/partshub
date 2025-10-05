"""
Contract test for GET /api/providers
Tests provider listing endpoint according to wizard feature requirements.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.contract
class TestProvidersContract:
    """Contract tests for provider listing endpoint"""

    def test_get_providers_requires_admin_auth(self, client: TestClient):
        """Test that provider listing requires admin authentication"""
        response = client.get("/api/providers")

        # Should fail with 401 unauthorized
        assert response.status_code == 401

    def test_get_providers_non_admin_forbidden(
        self, client: TestClient, user_auth_headers
    ):
        """Test that non-admin users cannot access provider listing"""
        response = client.get("/api/providers", headers=user_auth_headers)

        # Should fail with 403 forbidden
        assert response.status_code == 403

    def test_get_providers_with_admin_auth(self, client: TestClient, auth_headers):
        """Test provider listing with admin authentication"""
        response = client.get("/api/providers", headers=auth_headers)

        # Debug output if fails
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")

        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Empty list is valid (no providers seeded yet)
        # Each provider should have required schema fields
        for provider in data:
            assert "id" in provider
            assert "name" in provider
            assert "status" in provider
            assert "api_key_required" in provider
            assert isinstance(provider["status"], str)
            assert isinstance(provider["api_key_required"], bool)

    def test_get_providers_response_structure(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test response structure matches Provider schema"""
        # Seed a test provider
        from backend.src.models.wizard_provider import Provider

        test_provider = Provider(
            name="LCSC",
            adapter_class="LCSCAdapter",
            base_url="https://wmsc.lcsc.com/wmsc",
            status="active",
            api_key_required=False,
        )
        db_session.add(test_provider)
        db_session.commit()
        db_session.refresh(test_provider)

        response = client.get("/api/providers", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 1

        # Find our test provider
        lcsc_provider = next(p for p in data if p["name"] == "LCSC")

        # Verify complete schema
        assert lcsc_provider["id"] == test_provider.id
        assert lcsc_provider["name"] == "LCSC"
        assert lcsc_provider["status"] == "active"
        assert lcsc_provider["api_key_required"] is False

    def test_get_providers_filters_inactive_providers(
        self, client: TestClient, auth_headers, db_session
    ):
        """Test that inactive providers can be filtered or shown separately"""
        from backend.src.models.wizard_provider import Provider

        # Create active and inactive providers
        active_provider = Provider(
            name="Active Provider",
            adapter_class="ActiveAdapter",
            base_url="https://api.active.com",
            status="active",
            api_key_required=False,
        )
        inactive_provider = Provider(
            name="Inactive Provider",
            adapter_class="InactiveAdapter",
            base_url="https://api.inactive.com",
            status="inactive",
            api_key_required=True,
        )

        db_session.add_all([active_provider, inactive_provider])
        db_session.commit()

        response = client.get("/api/providers", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()

        # Both providers should be returned (filtering is a frontend concern)
        # But status field should accurately reflect state
        provider_names = [p["name"] for p in data]
        assert "Active Provider" in provider_names
        assert "Inactive Provider" in provider_names

        # Verify status values
        for provider in data:
            if provider["name"] == "Active Provider":
                assert provider["status"] == "active"
            elif provider["name"] == "Inactive Provider":
                assert provider["status"] == "inactive"
