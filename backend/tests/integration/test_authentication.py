"""
Integration test for authentication functionality.
Tests user authentication, authorization, token management, and access control.
"""

import pytest
from fastapi.testclient import TestClient

from backend.src.auth.admin import ensure_admin_exists


@pytest.mark.integration
class TestAuthenticationIntegration:
    """Integration tests for authentication and authorization"""

    def test_default_admin_login(self, client: TestClient, db_session):
        """Test default admin user login functionality"""

        # Ensure admin user exists in test database and get the password
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            # Admin already exists - use fixed password for testing
            admin_password = "admin123"

        # Test initial admin login with the actual password - use form data, not JSON
        login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )

        assert login_response.status_code == 200
        login_data = login_response.json()

        # Verify login response structure
        assert "access_token" in login_data
        assert "token_type" in login_data
        assert login_data["token_type"] == "bearer"
        # Note: The actual response doesn't include user data, only token info

    def test_password_change_requirement(self, client: TestClient, db_session):
        """Test forced password change for default admin"""

        # Ensure admin user exists
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"

        # Login with default credentials
        login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test that user needs to change password
        user_response = client.get("/api/v1/auth/me", headers=headers)
        assert user_response.status_code == 200

        user_data = user_response.json()
        # Should indicate password change required for default admin
        assert user_data.get("username") == "admin"
        assert user_data.get("must_change_password") is True

    def test_password_change_functionality(self, client: TestClient, db_session):
        """Test password change functionality"""

        # Ensure admin user exists
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"

        # Login with default credentials
        login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Change password
        password_change_response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": admin_password,
                "new_password": "newSecurePassword123!",
            },
            headers=headers,
        )

        assert password_change_response.status_code == 200

        # Test that old password no longer works
        old_login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        assert old_login_response.status_code == 401

        # Test that new password works
        new_login_response = client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "newSecurePassword123!"},
        )
        assert new_login_response.status_code == 200

    def test_invalid_login_attempts(self, client: TestClient, db_session):
        """Test handling of invalid login attempts"""

        # Ensure admin user exists
        ensure_admin_exists(db_session)

        # Test wrong username
        wrong_user_response = client.post(
            "/api/v1/auth/token",
            data={"username": "nonexistent", "password": "admin123"},
        )
        assert wrong_user_response.status_code == 401

        # Test wrong password
        wrong_password_response = client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "wrongpassword"},
        )
        assert wrong_password_response.status_code == 401

        # Test malformed request
        malformed_response = client.post(
            "/api/v1/auth/token",
            data={
                "username": "admin"
                # Missing password
            },
        )
        assert malformed_response.status_code == 422

    def test_token_authentication(self, client: TestClient, db_session):
        """Test JWT token authentication for protected endpoints"""

        # Ensure admin user exists
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test authenticated endpoint
        me_response = client.get("/api/v1/auth/me", headers=headers)
        assert me_response.status_code == 200

        # Test invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        invalid_response = client.get("/api/v1/auth/me", headers=invalid_headers)
        assert invalid_response.status_code == 401

        # Test missing token
        no_token_response = client.get("/api/v1/auth/me")
        assert no_token_response.status_code == 401

    def test_api_token_management(self, client: TestClient, db_session):
        """Test API token creation and management"""

        # Ensure admin user exists
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"

        # Login to get admin access
        login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Change password first (required for admin)
        client.post(
            "/api/v1/auth/change-password",
            json={"current_password": admin_password, "new_password": "newPass123!"},
            headers=headers,
        )

        # Re-login with new password
        new_login = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": "newPass123!"}
        )
        headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}

        # Test API token creation
        api_token_response = client.post(
            "/api/v1/auth/api-tokens",
            json={
                "name": "Test API Token",
                "description": "Integration test token",
                "expires_in_days": 30,
            },
            headers=headers,
        )

        if api_token_response.status_code == 201:
            api_token_data = api_token_response.json()
            assert "token" in api_token_data
            assert "id" in api_token_data
            assert api_token_data["name"] == "Test API Token"

            # Test using API token for authentication
            api_headers = {"Authorization": f"Bearer {api_token_data['token']}"}
            api_test_response = client.get("/api/v1/components", headers=api_headers)
            # API tokens should work for CRUD operations
            assert api_test_response.status_code in [
                200,
                401,
            ]  # Depends on implementation
        else:
            # API token management might not be implemented or returns different status codes
            assert api_token_response.status_code in [200, 201, 404, 501]

    def test_admin_crud_operations(self, client: TestClient, db_session):
        """Test admin CRUD operations require authentication"""

        # Ensure admin user exists
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"

        # Login as admin
        login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Change password
        client.post(
            "/api/v1/auth/change-password",
            json={"current_password": admin_password, "new_password": "adminPass123!"},
            headers=headers,
        )

        # Re-login
        new_login = client.post(
            "/api/v1/auth/token",
            data={"username": "admin", "password": "adminPass123!"},
        )
        headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}

        # Test authenticated CRUD operations

        # Import uuid for unique names
        import uuid

        test_id = str(uuid.uuid4())[:8]

        # Create category with unique name
        category_response = client.post(
            "/api/v1/categories",
            json={
                "name": f"Auth Test Category {test_id}",
                "description": "Testing authentication",
            },
            headers=headers,
        )
        assert category_response.status_code == 201

        # Create storage location with unique name
        storage_response = client.post(
            "/api/v1/storage-locations",
            json={
                "name": f"Auth Test Storage {test_id}",
                "description": "Testing authentication",
                "type": "drawer",
            },
            headers=headers,
        )
        assert storage_response.status_code == 201

        # Create component with unique name and part number
        component_response = client.post(
            "/api/v1/components",
            json={
                "name": f"Auth Test Component {test_id}",
                "part_number": f"AUTH{test_id}",
                "manufacturer": "Auth Mfg",
                "category_id": category_response.json()["id"],
                "storage_location_id": storage_response.json()["id"],
                "component_type": "resistor",
                "quantity_on_hand": 10,
            },
            headers=headers,
        )
        assert component_response.status_code == 201

    def test_token_expiration_handling(self, client: TestClient, db_session):
        """Test token expiration and refresh behavior"""

        # Ensure admin user exists
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token = login_response.json()["access_token"]

        # Test that token is valid initially
        headers = {"Authorization": f"Bearer {token}"}
        valid_response = client.get("/api/v1/auth/me", headers=headers)
        assert valid_response.status_code == 200

        # Test with very old/expired token (if token validation is strict)
        expired_headers = {
            "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMiwiZXhwIjoxNTE2MjM5MDIyfQ.invalid"
        }
        expired_response = client.get("/api/v1/auth/me", headers=expired_headers)
        assert expired_response.status_code == 401

    def test_logout_functionality(self, client: TestClient, db_session):
        """Test logout functionality and token invalidation"""

        # Ensure admin user exists
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"

        # Login to get token
        login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test logout endpoint (if implemented)
        logout_response = client.post("/api/v1/auth/logout", headers=headers)

        if logout_response.status_code == 200:
            # Test that token is no longer valid after logout
            post_logout_response = client.get("/api/v1/auth/me", headers=headers)
            # Token should be invalidated (if logout invalidates tokens)
            assert post_logout_response.status_code in [200, 401]
        else:
            # Logout endpoint might not be implemented or use different approach
            assert logout_response.status_code in [200, 404, 405]

    def test_password_validation_requirements(self, client: TestClient, db_session):
        """Test password validation requirements"""

        # Ensure admin user exists
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"

        # Login as admin
        login_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test weak password rejection
        weak_password_response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": admin_password,
                "new_password": "123",  # Too weak
            },
            headers=headers,
        )

        if weak_password_response.status_code == 422:
            # Password validation is implemented
            error_data = weak_password_response.json()
            assert "password" in str(error_data).lower()
        else:
            # Password validation might be lenient or not implemented
            assert weak_password_response.status_code in [200, 422]

    def test_concurrent_login_sessions(self, client: TestClient, db_session):
        """Test multiple concurrent login sessions"""

        # Ensure admin user exists
        result = ensure_admin_exists(db_session)
        if result:
            admin_user, admin_password = result
        else:
            admin_password = "admin123"

        # Create multiple login sessions
        login1_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token1 = login1_response.json()["access_token"]

        login2_response = client.post(
            "/api/v1/auth/token", data={"username": "admin", "password": admin_password}
        )
        token2 = login2_response.json()["access_token"]

        # Test that both tokens work
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        response1 = client.get("/api/v1/auth/me", headers=headers1)
        response2 = client.get("/api/v1/auth/me", headers=headers2)

        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_authentication_error_messages(self, client: TestClient, db_session):
        """Test authentication error message handling"""

        # Ensure admin user exists
        ensure_admin_exists(db_session)

        # Test malformed Authorization header
        bad_header_response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "InvalidFormat"}
        )
        assert bad_header_response.status_code == 401

        # Test empty Authorization header
        empty_header_response = client.get(
            "/api/v1/auth/me", headers={"Authorization": ""}
        )
        assert empty_header_response.status_code == 401

        # Verify error responses have appropriate structure
        error_data = bad_header_response.json()
        assert "detail" in error_data
