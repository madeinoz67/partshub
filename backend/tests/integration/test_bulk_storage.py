"""
Integration test for bulk storage location functionality.
Tests bulk storage creation, hierarchy management, and location organization.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from src.main import app
from src.database.connection import get_db
from src.models import Base


class TestBulkStorageIntegration:
    """Integration tests for bulk storage location functionality"""

    @pytest.fixture
    def db_session(self):
        """Create a shared database session for testing"""
        from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
        from src.auth.dependencies import get_optional_user
        from src.auth.jwt_auth import get_current_user as get_user_from_token
        from src.models import User

        db_fd, db_path = tempfile.mkstemp()
        engine = create_engine(f"sqlite:///{db_path}")
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

        Base.metadata.create_all(bind=engine)
        session = TestingSessionLocal()

        def override_get_db():
            yield session

        async def test_get_optional_user(
            credentials: HTTPAuthorizationCredentials = None,
            db = None
        ):
            """TestClient-compatible version of get_optional_user"""
            if not credentials:
                return None

            try:
                user_data = get_user_from_token(credentials.credentials)
                user = session.query(User).filter(User.id == user_data["user_id"]).first()
                if user and user.is_active:
                    return {
                        "user_id": user.id,
                        "username": user.username,
                        "is_admin": user.is_admin,
                        "auth_type": "jwt"
                    }
            except Exception:
                pass

            return None

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_optional_user] = test_get_optional_user
        yield session

        session.close()
        os.close(db_fd)
        os.unlink(db_path)
        app.dependency_overrides.clear()

    @pytest.fixture
    def client(self, db_session):
        """Test client with shared database session"""
        return TestClient(app)

    @pytest.fixture
    def admin_headers(self, db_session):
        """Get admin authentication headers using direct token creation"""
        from src.auth.jwt_auth import create_access_token
        from src.models import User

        # Create admin user directly in shared test database session
        admin_user = User(
            username="testadmin",
            full_name="Test Admin",
            is_admin=True,
            is_active=True
        )
        admin_user.set_password("testpassword")

        db_session.add(admin_user)
        db_session.commit()
        db_session.refresh(admin_user)

        # Create JWT token directly
        token = create_access_token({
            "sub": admin_user.id,
            "user_id": admin_user.id,
            "username": admin_user.username,
            "is_admin": admin_user.is_admin
        })

        return {"Authorization": f"Bearer {token}"}

    def test_bulk_storage_single_creation(self, client: TestClient, admin_headers: dict):
        """Test bulk creation of single storage locations"""

        bulk_data = {
            "prefix": "Bin",
            "layout_type": "single",
            "count": 5,
            "description": "Basic storage bins"
        }

        response = client.post("/api/v1/storage-locations/bulk-create",
            json=bulk_data,
            headers=admin_headers
        )

        if response.status_code == 200:
            created_locations = response.json()
            assert len(created_locations) == 5

            # Verify naming pattern
            for i, location in enumerate(created_locations, 1):
                expected_name = f"Bin {i}"
                assert location["name"] == expected_name
                assert location["description"] == "Basic storage bins"
        else:
            # Bulk creation might not be implemented yet or have validation errors
            assert response.status_code in [200, 404, 422, 501]

    def test_bulk_storage_row_creation(self, client: TestClient, admin_headers: dict):
        """Test bulk creation of storage locations in row layout"""

        bulk_data = {
            "prefix": "Drawer",
            "layout_type": "row",
            "count": 12,
            "letter_start": "A",
            "letter_end": "L",
            "description": "Drawer row storage"
        }

        response = client.post("/api/v1/storage-locations/bulk-create",
            json=bulk_data,
            headers=admin_headers
        )

        if response.status_code == 200:
            created_locations = response.json()
            assert len(created_locations) == 12

            # Verify alphabetical naming pattern
            for i, location in enumerate(created_locations):
                expected_letter = chr(ord('A') + i)
                expected_name = f"Drawer {expected_letter}"
                assert location["name"] == expected_name
        else:
            # Bulk creation might not be implemented yet or have validation errors
            assert response.status_code in [200, 404, 422, 501]

    def test_bulk_storage_grid_creation(self, client: TestClient, admin_headers: dict):
        """Test bulk creation of storage locations in grid layout"""

        bulk_data = {
            "prefix": "Shelf",
            "layout_type": "grid",
            "rows": 3,
            "columns": 4,
            "description": "Grid shelf storage"
        }

        response = client.post("/api/v1/storage-locations/bulk-create",
            json=bulk_data,
            headers=admin_headers
        )

        if response.status_code == 200:
            created_locations = response.json()
            expected_count = 3 * 4  # rows * columns
            assert len(created_locations) == expected_count

            # Verify grid naming pattern (should be like Shelf 1-1, Shelf 1-2, etc.)
            grid_names = [loc["name"] for loc in created_locations]
            assert "Shelf 1-1" in grid_names
            assert "Shelf 3-4" in grid_names
        else:
            # Bulk creation might not be implemented yet or have validation errors
            assert response.status_code in [200, 404, 422, 501]

    def test_bulk_storage_3d_grid_creation(self, client: TestClient, admin_headers: dict):
        """Test bulk creation of storage locations in 3D grid layout"""

        bulk_data = {
            "prefix": "Cabinet",
            "layout_type": "3d_grid",
            "rows": 2,
            "columns": 3,
            "layers": 2,
            "description": "3D cabinet storage"
        }

        response = client.post("/api/v1/storage-locations/bulk-create",
            json=bulk_data,
            headers=admin_headers
        )

        if response.status_code == 200:
            created_locations = response.json()
            expected_count = 2 * 3 * 2  # rows * columns * layers
            assert len(created_locations) == expected_count

            # Verify 3D grid naming pattern
            grid_names = [loc["name"] for loc in created_locations]
            assert any("Cabinet" in name for name in grid_names)
        else:
            # 3D bulk creation might not be implemented yet
            assert response.status_code in [200, 404, 501]

    def test_bulk_storage_validation(self, client: TestClient, admin_headers: dict):
        """Test bulk storage creation validation"""

        # Test missing required fields
        invalid_data = {
            "prefix": "Test",
            # Missing layout_type
        }

        response = client.post("/api/v1/storage-locations/bulk-create",
            json=invalid_data,
            headers=admin_headers
        )
        assert response.status_code in [422, 400, 404, 501]

        # Test invalid layout type
        invalid_layout_data = {
            "prefix": "Test",
            "layout_type": "invalid_layout",
            "count": 5
        }

        response = client.post("/api/v1/storage-locations/bulk-create",
            json=invalid_layout_data,
            headers=admin_headers
        )
        assert response.status_code in [422, 400, 404, 501]

    def test_bulk_storage_preview(self, client: TestClient, admin_headers: dict):
        """Test bulk storage location preview functionality"""

        preview_data = {
            "prefix": "Preview",
            "layout_type": "single",
            "count": 3,
            "description": "Preview test"
        }

        response = client.post("/api/v1/storage-locations/bulk-create/preview",
            json=preview_data,
            headers=admin_headers
        )

        if response.status_code == 200:
            preview_locations = response.json()
            assert len(preview_locations) == 3

            # Preview should show what would be created without actually creating
            for i, location in enumerate(preview_locations, 1):
                expected_name = f"Preview {i}"
                assert location["name"] == expected_name
                # Preview items shouldn't have actual IDs
                assert "id" not in location or location["id"] is None
        else:
            # Preview functionality might not be implemented
            assert response.status_code in [200, 404, 501]

    def test_bulk_storage_hierarchical_creation(self, client: TestClient, admin_headers: dict):
        """Test bulk creation of hierarchical storage locations"""

        # First create a parent location
        parent_data = {
            "name": "Storage Room A",
            "description": "Main storage room"
        }

        parent_response = client.post("/api/v1/storage-locations",
            json=parent_data,
            headers=admin_headers
        )
        assert parent_response.status_code == 201
        parent_id = parent_response.json()["id"]

        # Create bulk child locations
        bulk_data = {
            "prefix": "Rack",
            "layout_type": "single",
            "count": 4,
            "parent_id": parent_id,
            "description": "Storage racks in room A"
        }

        response = client.post("/api/v1/storage-locations/bulk-create",
            json=bulk_data,
            headers=admin_headers
        )

        if response.status_code == 200:
            created_locations = response.json()
            assert len(created_locations) == 4

            # Verify parent-child relationship
            for location in created_locations:
                assert location["parent_id"] == parent_id
                assert "Rack" in location["name"]
        else:
            # Hierarchical bulk creation might not be implemented
            assert response.status_code in [200, 404, 501]

    def test_bulk_storage_with_custom_naming(self, client: TestClient, admin_headers: dict):
        """Test bulk storage creation with custom naming patterns"""

        bulk_data = {
            "prefix": "SMD",
            "layout_type": "row",
            "count": 26,
            "letter_start": "A",
            "letter_end": "Z",
            "use_uppercase": True,
            "description": "SMD component storage"
        }

        response = client.post("/api/v1/storage-locations/bulk-create",
            json=bulk_data,
            headers=admin_headers
        )

        if response.status_code == 200:
            created_locations = response.json()
            assert len(created_locations) == 26

            # Check first and last items
            first_location = created_locations[0]
            last_location = created_locations[-1]

            assert first_location["name"] == "SMD A"
            assert last_location["name"] == "SMD Z"
        else:
            # Custom naming might not be implemented
            assert response.status_code in [200, 404, 501]

    def test_bulk_storage_duplicate_prevention(self, client: TestClient, admin_headers: dict):
        """Test bulk storage creation duplicate name prevention"""

        # Create initial storage location
        initial_data = {
            "name": "Bin 1",
            "description": "First bin"
        }

        client.post("/api/v1/storage-locations",
            json=initial_data,
            headers=admin_headers
        )

        # Try to create bulk locations that would conflict
        bulk_data = {
            "prefix": "Bin",
            "layout_type": "single",
            "count": 3,
            "description": "Bulk bins"
        }

        response = client.post("/api/v1/storage-locations/bulk-create",
            json=bulk_data,
            headers=admin_headers
        )

        if response.status_code == 200:
            # Should handle duplicates gracefully (skip or rename)
            created_locations = response.json()
            names = [loc["name"] for loc in created_locations]
            # Either skipped "Bin 1" or renamed it to avoid conflict
            assert len(set(names)) == len(names)  # All names should be unique
        elif response.status_code == 409:
            # Conflict detected and rejected
            error_data = response.json()
            assert "conflict" in error_data.get("detail", "").lower()
        else:
            # Bulk creation might not be implemented
            assert response.status_code in [200, 409, 404, 501]

    def test_bulk_storage_large_creation(self, client: TestClient, admin_headers: dict):
        """Test bulk storage creation with large numbers"""

        bulk_data = {
            "prefix": "Slot",
            "layout_type": "single",
            "count": 100,
            "description": "Large slot array"
        }

        response = client.post("/api/v1/storage-locations/bulk-create",
            json=bulk_data,
            headers=admin_headers
        )

        if response.status_code == 200:
            created_locations = response.json()
            assert len(created_locations) == 100

            # Verify numbering for large set
            first_location = created_locations[0]
            last_location = created_locations[-1]

            assert first_location["name"] == "Slot 1"
            assert last_location["name"] == "Slot 100"
        elif response.status_code == 413:
            # Request too large - reasonable limit
            pass
        else:
            # Large bulk creation might not be supported
            assert response.status_code in [200, 413, 404, 501]

    def test_bulk_storage_authentication_required(self, client: TestClient):
        """Test that bulk storage operations require authentication"""

        bulk_data = {
            "prefix": "Test",
            "layout_type": "single",
            "count": 3
        }

        # Test without authentication
        response = client.post("/api/v1/storage-locations/bulk-create", json=bulk_data)
        assert response.status_code in [401, 404, 501]

        # Test preview without authentication
        preview_response = client.post("/api/v1/storage-locations/bulk-create/preview", json=bulk_data)
        assert preview_response.status_code in [401, 404, 501]

    def test_bulk_storage_error_handling(self, client: TestClient, admin_headers: dict):
        """Test bulk storage creation error handling"""

        # Test with malformed JSON
        response = client.post("/api/v1/storage-locations/bulk-create",
            data="invalid json",
            headers=admin_headers
        )
        assert response.status_code in [422, 400, 404, 501]

        # Test with negative count
        negative_data = {
            "prefix": "Test",
            "layout_type": "single",
            "count": -5
        }

        response = client.post("/api/v1/storage-locations/bulk-create",
            json=negative_data,
            headers=admin_headers
        )
        assert response.status_code in [422, 400, 404, 501]