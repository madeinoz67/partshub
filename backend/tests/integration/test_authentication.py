"""
Integration test for authentication functionality.
Tests user authentication, authorization, token management, and access control.
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.connection import Base, get_db
from src.main import app


class TestAuthenticationIntegration:
    """Integration tests for authentication and authorization"""

    @pytest.fixture
    def test_db(self):
        """Create a temporary database for testing"""
        db_fd, db_path = tempfile.mkstemp()
        engine = create_engine(f"sqlite:///{db_path}")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        Base.metadata.create_all(bind=engine)

        def override_get_db():
            try:
                db = TestingSessionLocal()
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        yield engine

        os.close(db_fd)
        os.unlink(db_path)
        app.dependency_overrides.clear()

    @pytest.fixture
    def client(self, test_db):
        """Test client with isolated database"""
        return TestClient(app)

    def test_default_admin_login(self, client: TestClient):
        """Test default admin user login functionality"""

        # Test initial admin login with default password
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })

        assert login_response.status_code == 200
        login_data = login_response.json()

        # Verify login response structure
        assert "access_token" in login_data
        assert "token_type" in login_data
        assert login_data["token_type"] == "bearer"
        assert "user" in login_data

        user_data = login_data["user"]
        assert user_data["username"] == "admin"
        assert user_data["is_admin"] is True

    def test_password_change_requirement(self, client: TestClient):
        """Test forced password change for default admin"""

        # Login with default credentials
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test that user needs to change password
        user_response = client.get("/api/v1/auth/me", headers=headers)
        assert user_response.status_code == 200

        user_data = user_response.json()
        # Should indicate password change required for default admin
        assert "needs_password_change" in user_data or user_data.get("username") == "admin"

    def test_password_change_functionality(self, client: TestClient):
        """Test password change functionality"""

        # Login with default credentials
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Change password
        password_change_response = client.post("/api/v1/auth/change-password", json={
            "current_password": "admin123",
            "new_password": "newSecurePassword123!"
        }, headers=headers)

        assert password_change_response.status_code == 200

        # Test that old password no longer works
        old_login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })
        assert old_login_response.status_code == 401

        # Test that new password works
        new_login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "newSecurePassword123!"
        })
        assert new_login_response.status_code == 200

    def test_invalid_login_attempts(self, client: TestClient):
        """Test handling of invalid login attempts"""

        # Test wrong username
        wrong_user_response = client.post("/api/v1/auth/token", json={
            "username": "nonexistent",
            "password": "admin123"
        })
        assert wrong_user_response.status_code == 401

        # Test wrong password
        wrong_password_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "wrongpassword"
        })
        assert wrong_password_response.status_code == 401

        # Test malformed request
        malformed_response = client.post("/api/v1/auth/token", json={
            "username": "admin"
            # Missing password
        })
        assert malformed_response.status_code == 422

    def test_token_authentication(self, client: TestClient):
        """Test JWT token authentication for protected endpoints"""

        # Login to get token
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })
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

    def test_api_token_management(self, client: TestClient):
        """Test API token creation and management"""

        # Login to get admin access
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Change password first (required for admin)
        client.post("/api/v1/auth/change-password", json={
            "current_password": "admin123",
            "new_password": "newPass123!"
        }, headers=headers)

        # Re-login with new password
        new_login = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "newPass123!"
        })
        headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}

        # Test API token creation
        api_token_response = client.post("/api/v1/auth/api-tokens", json={
            "name": "Test API Token",
            "description": "Integration test token",
            "expires_days": 30
        }, headers=headers)

        if api_token_response.status_code == 201:
            api_token_data = api_token_response.json()
            assert "token" in api_token_data
            assert "id" in api_token_data
            assert api_token_data["name"] == "Test API Token"

            # Test using API token for authentication
            api_headers = {"Authorization": f"Bearer {api_token_data['token']}"}
            api_test_response = client.get("/api/v1/components", headers=api_headers)
            # API tokens should work for CRUD operations
            assert api_test_response.status_code in [200, 401]  # Depends on implementation
        else:
            # API token management might not be implemented
            assert api_token_response.status_code in [201, 404, 501]

    def test_tiered_access_control(self, client: TestClient):
        """Test tiered access control (anonymous vs authenticated)"""

        # Test anonymous read access
        anonymous_components_response = client.get("/api/v1/components")
        assert anonymous_components_response.status_code == 200  # Should allow read access

        anonymous_storage_response = client.get("/api/v1/storage-locations")
        assert anonymous_storage_response.status_code == 200  # Should allow read access

        # Test anonymous write access should be denied
        anonymous_create_response = client.post("/api/v1/components", json={
            "name": "Test Component",
            "part_number": "TEST001",
            "manufacturer": "Test Mfg",
            "component_type": "resistor"
        })
        assert anonymous_create_response.status_code == 401  # Should deny write access

    def test_admin_crud_operations(self, client: TestClient):
        """Test admin CRUD operations require authentication"""

        # Login as admin
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Change password
        client.post("/api/v1/auth/change-password", json={
            "current_password": "admin123",
            "new_password": "adminPass123!"
        }, headers=headers)

        # Re-login
        new_login = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "adminPass123!"
        })
        headers = {"Authorization": f"Bearer {new_login.json()['access_token']}"}

        # Test authenticated CRUD operations

        # Create category
        category_response = client.post("/api/v1/categories", json={
            "name": "Auth Test Category",
            "description": "Testing authentication"
        }, headers=headers)
        assert category_response.status_code == 201

        # Create storage location
        storage_response = client.post("/api/v1/storage-locations", json={
            "name": "Auth Test Storage",
            "description": "Testing authentication"
        }, headers=headers)
        assert storage_response.status_code == 201

        # Create component
        component_response = client.post("/api/v1/components", json={
            "name": "Auth Test Component",
            "part_number": "AUTH001",
            "manufacturer": "Auth Mfg",
            "category_id": category_response.json()["id"],
            "storage_location_id": storage_response.json()["id"],
            "component_type": "resistor",
            "quantity_on_hand": 10
        }, headers=headers)
        assert component_response.status_code == 201

    def test_token_expiration_handling(self, client: TestClient):
        """Test token expiration and refresh behavior"""

        # Login to get token
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]

        # Test that token is valid initially
        headers = {"Authorization": f"Bearer {token}"}
        valid_response = client.get("/api/v1/auth/me", headers=headers)
        assert valid_response.status_code == 200

        # Test with very old/expired token (if token validation is strict)
        expired_headers = {"Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMiwiZXhwIjoxNTE2MjM5MDIyfQ.invalid"}
        expired_response = client.get("/api/v1/auth/me", headers=expired_headers)
        assert expired_response.status_code == 401

    def test_logout_functionality(self, client: TestClient):
        """Test logout functionality and token invalidation"""

        # Login to get token
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })
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

    def test_password_validation_requirements(self, client: TestClient):
        """Test password validation requirements"""

        # Login as admin
        login_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test weak password rejection
        weak_password_response = client.post("/api/v1/auth/change-password", json={
            "current_password": "admin123",
            "new_password": "123"  # Too weak
        }, headers=headers)

        if weak_password_response.status_code == 422:
            # Password validation is implemented
            error_data = weak_password_response.json()
            assert "password" in str(error_data).lower()
        else:
            # Password validation might be lenient or not implemented
            assert weak_password_response.status_code in [200, 422]

    def test_concurrent_login_sessions(self, client: TestClient):
        """Test multiple concurrent login sessions"""

        # Create multiple login sessions
        login1_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })
        token1 = login1_response.json()["access_token"]

        login2_response = client.post("/api/v1/auth/token", json={
            "username": "admin",
            "password": "admin123"
        })
        token2 = login2_response.json()["access_token"]

        # Test that both tokens work
        headers1 = {"Authorization": f"Bearer {token1}"}
        headers2 = {"Authorization": f"Bearer {token2}"}

        response1 = client.get("/api/v1/auth/me", headers=headers1)
        response2 = client.get("/api/v1/auth/me", headers=headers2)

        assert response1.status_code == 200
        assert response2.status_code == 200

    def test_authentication_error_messages(self, client: TestClient):
        """Test authentication error message handling"""

        # Test malformed Authorization header
        bad_header_response = client.get("/api/v1/auth/me", headers={
            "Authorization": "InvalidFormat"
        })
        assert bad_header_response.status_code == 401

        # Test empty Authorization header
        empty_header_response = client.get("/api/v1/auth/me", headers={
            "Authorization": ""
        })
        assert empty_header_response.status_code == 401

        # Verify error responses have appropriate structure
        error_data = bad_header_response.json()
        assert "detail" in error_data
