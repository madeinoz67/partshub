"""
Integration test for admin-only access enforcement in wizard.
Tests that all wizard endpoints require admin role.
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
class TestWizardAuth:
    """Integration tests for wizard admin-only access control"""

    def test_wizard_endpoints_require_admin(
        self,
        client: TestClient,
        user_auth_headers,
        db_session,
    ):
        """
        Test admin-only access enforcement:
        1. Create non-admin user with JWT token
        2. GET /api/providers with non-admin token -> 403 Forbidden
        3. POST /api/wizard/components with non-admin token -> 403 Forbidden
        4. Verify all wizard endpoints require admin role
        """
        from backend.src.models.provider import ComponentDataProvider

        # Create test provider for endpoint testing
        provider = ComponentDataProvider(
            name="LCSC",
            api_endpoint="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        # Step 1: Non-admin user authenticated via user_auth_headers fixture

        # Step 2: Test GET /api/providers with non-admin token
        providers_response = client.get("/api/providers", headers=user_auth_headers)
        assert providers_response.status_code == 403

        # Test GET /api/providers/{id}/search with non-admin token
        search_response = client.get(
            f"/api/providers/{provider.id}/search?query=test&limit=10",
            headers=user_auth_headers,
        )
        assert search_response.status_code == 403

        # Test GET /api/wizard/manufacturers/search with non-admin token
        mfg_response = client.get(
            "/api/wizard/manufacturers/search?query=TI&limit=10",
            headers=user_auth_headers,
        )
        assert mfg_response.status_code == 403

        # Test GET /api/wizard/footprints/search with non-admin token
        footprint_response = client.get(
            "/api/wizard/footprints/search?query=SOIC&limit=10",
            headers=user_auth_headers,
        )
        assert footprint_response.status_code == 403

        # Step 3: Test POST /api/wizard/components with non-admin token
        component_data = {
            "name": "Unauthorized Component",
            "description": "Should be blocked",
            "part_type": "local",
        }

        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=user_auth_headers,
        )
        assert create_response.status_code == 403

    def test_wizard_endpoints_require_authentication(
        self,
        client: TestClient,
        db_session,
    ):
        """Test that wizard endpoints require authentication (not just admin)"""
        from backend.src.models.provider import ComponentDataProvider

        provider = ComponentDataProvider(
            name="LCSC",
            api_endpoint="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)
        db_session.commit()
        db_session.refresh(provider)

        # Test without any authentication headers

        # GET /api/providers
        providers_response = client.get("/api/providers")
        assert providers_response.status_code == 401

        # GET /api/providers/{id}/search
        search_response = client.get(
            f"/api/providers/{provider.id}/search?query=test&limit=10"
        )
        assert search_response.status_code == 401

        # GET /api/wizard/manufacturers/search
        mfg_response = client.get("/api/wizard/manufacturers/search?query=TI&limit=10")
        assert mfg_response.status_code == 401

        # GET /api/wizard/footprints/search
        footprint_response = client.get("/api/wizard/footprints/search?query=SOIC&limit=10")
        assert footprint_response.status_code == 401

        # POST /api/wizard/components
        component_data = {
            "name": "Unauthenticated Component",
            "description": "Should be blocked",
            "part_type": "local",
        }
        create_response = client.post("/api/wizard/components", json=component_data)
        assert create_response.status_code == 401

    def test_admin_user_can_access_all_wizard_endpoints(
        self,
        client: TestClient,
        auth_headers,
        db_session,
    ):
        """Test that admin users can access all wizard endpoints"""
        from backend.src.models.provider import ComponentDataProvider
        from backend.src.models.component import Component

        # Seed test data
        provider = ComponentDataProvider(
            name="LCSC",
            api_endpoint="https://api.lcsc.com",
            status="active",
            api_key_required=False,
        )
        db_session.add(provider)

        component = Component(name="Test", manufacturer="STMicroelectronics")
        db_session.add(component)
        db_session.commit()
        db_session.refresh(provider)

        # Admin can access GET /api/providers
        providers_response = client.get("/api/providers", headers=auth_headers)
        assert providers_response.status_code == 200

        # Admin can access GET /api/wizard/manufacturers/search
        mfg_response = client.get(
            "/api/wizard/manufacturers/search?query=STM&limit=10",
            headers=auth_headers,
        )
        assert mfg_response.status_code == 200

        # Admin can access GET /api/wizard/footprints/search
        footprint_response = client.get(
            "/api/wizard/footprints/search?query=SOIC&limit=10",
            headers=auth_headers,
        )
        assert footprint_response.status_code == 200

        # Admin can access POST /api/wizard/components
        component_data = {
            "name": "Admin Component",
            "description": "Created by admin",
            "part_type": "local",
        }
        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )
        assert create_response.status_code == 201

    def test_resource_endpoints_require_admin(
        self,
        client: TestClient,
        user_auth_headers,
    ):
        """Test that resource-related endpoints require admin access"""
        # Test GET /api/resources/{id}/status with non-admin token
        resource_status_response = client.get(
            "/api/resources/1/status",
            headers=user_auth_headers,
        )
        assert resource_status_response.status_code == 403

        # Test POST /api/provider-links/{id}/resources with non-admin token
        resource_data = {
            "type": "datasheet",
            "url": "https://example.com/datasheet.pdf",
            "file_name": "datasheet.pdf",
        }
        add_resource_response = client.post(
            "/api/provider-links/1/resources",
            json=resource_data,
            headers=user_auth_headers,
        )
        assert add_resource_response.status_code == 403

    def test_invalid_token_rejected(
        self,
        client: TestClient,
    ):
        """Test that invalid authentication tokens are rejected"""
        invalid_headers = {"Authorization": "Bearer invalid_token_12345"}

        # All wizard endpoints should reject invalid token
        providers_response = client.get("/api/providers", headers=invalid_headers)
        assert providers_response.status_code == 401

        mfg_response = client.get(
            "/api/wizard/manufacturers/search?query=TI&limit=10",
            headers=invalid_headers,
        )
        assert mfg_response.status_code == 401

        component_data = {
            "name": "Invalid Token Component",
            "description": "Should be blocked",
            "part_type": "local",
        }
        create_response = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=invalid_headers,
        )
        assert create_response.status_code == 401

    def test_expired_token_rejected(
        self,
        client: TestClient,
        db_session,
    ):
        """Test that expired tokens are rejected (if token expiry is implemented)"""
        # This test assumes JWT tokens have expiry
        # If not implemented, this test will be skipped
        # For now, test with malformed/old token format

        expired_headers = {
            "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE1MTYyMzkwMjJ9.invalid"
        }

        providers_response = client.get("/api/providers", headers=expired_headers)
        # Should be rejected (401 or 403)
        assert providers_response.status_code in [401, 403]

    def test_role_based_access_control_enforced(
        self,
        client: TestClient,
        auth_headers,
        user_auth_headers,
        db_session,
    ):
        """Test that admin and non-admin users have different access levels"""
        from backend.src.models.component import Component

        # Seed data
        component = Component(name="Test", manufacturer="Test Mfg")
        db_session.add(component)
        db_session.commit()

        # Admin can access manufacturer search
        admin_mfg_response = client.get(
            "/api/wizard/manufacturers/search?query=Test&limit=10",
            headers=auth_headers,
        )
        assert admin_mfg_response.status_code == 200

        # Non-admin cannot access manufacturer search
        user_mfg_response = client.get(
            "/api/wizard/manufacturers/search?query=Test&limit=10",
            headers=user_auth_headers,
        )
        assert user_mfg_response.status_code == 403

        # Admin can create component
        component_data = {
            "name": "Admin Created",
            "description": "By admin",
            "part_type": "local",
        }
        admin_create = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=auth_headers,
        )
        assert admin_create.status_code == 201

        # Non-admin cannot create component
        user_create = client.post(
            "/api/wizard/components",
            json=component_data,
            headers=user_auth_headers,
        )
        assert user_create.status_code == 403
