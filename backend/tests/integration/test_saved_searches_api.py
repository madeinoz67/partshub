"""
Integration tests for Saved Searches API endpoints
"""

import pytest

from backend.src.models import User


@pytest.mark.integration
class TestSavedSearchesAPI:
    """Test saved searches API endpoints"""

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user"""
        user = User(
            username="searchuser",
            full_name="Search User",
            is_active=True,
            is_admin=False,
        )
        user.set_password("searchpass123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def auth_headers(self, test_user, client):
        """Get authentication headers for test user"""
        # Login to get token
        response = client.post(
            "/api/v1/auth/token",
            data={"username": "searchuser", "password": "searchpass123"},
        )
        assert response.status_code == 200
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture
    def sample_search_params(self):
        """Sample search parameters"""
        return {
            "search": "resistor",
            "component_type": "resistor",
            "stock_status": "low",
            "tags": ["SMD"],
            "sort_by": "name",
            "sort_order": "asc",
        }

    def test_create_saved_search(self, client, auth_headers, sample_search_params):
        """Test POST /api/v1/saved-searches"""
        response = client.post(
            "/api/v1/saved-searches",
            json={
                "name": "Low Stock Resistors",
                "description": "Find SMD resistors with low stock",
                "search_parameters": sample_search_params,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Low Stock Resistors"
        assert data["description"] == "Find SMD resistors with low stock"
        assert data["search_parameters"] == sample_search_params
        assert "id" in data
        assert "created_at" in data
        assert data["last_used_at"] is None

    def test_create_saved_search_without_description(
        self, client, auth_headers, sample_search_params
    ):
        """Test creating search without optional description"""
        response = client.post(
            "/api/v1/saved-searches",
            json={"name": "Simple Search", "search_parameters": sample_search_params},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Simple Search"
        assert data["description"] is None

    def test_create_saved_search_unauthorized(self, client, sample_search_params):
        """Test creating search without authentication"""
        response = client.post(
            "/api/v1/saved-searches",
            json={"name": "Test Search", "search_parameters": sample_search_params},
        )

        assert response.status_code == 401

    def test_create_saved_search_invalid_data(self, client, auth_headers):
        """Test creating search with invalid data"""
        response = client.post(
            "/api/v1/saved-searches",
            json={"name": "Test Search"},  # Missing search_parameters
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_list_saved_searches(self, client, auth_headers, sample_search_params):
        """Test GET /api/v1/saved-searches"""
        # Create some searches
        for i in range(3):
            client.post(
                "/api/v1/saved-searches",
                json={
                    "name": f"Search {i}",
                    "search_parameters": sample_search_params,
                },
                headers=auth_headers,
            )

        # List searches
        response = client.get("/api/v1/saved-searches", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all("name" in s for s in data)

    def test_list_saved_searches_pagination(
        self, client, auth_headers, sample_search_params
    ):
        """Test pagination of saved searches"""
        # Create 10 searches
        for i in range(10):
            client.post(
                "/api/v1/saved-searches",
                json={
                    "name": f"Search {i:02d}",
                    "search_parameters": sample_search_params,
                },
                headers=auth_headers,
            )

        # Get first page
        response = client.get(
            "/api/v1/saved-searches?limit=5&offset=0", headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 5

        # Get second page
        response = client.get(
            "/api/v1/saved-searches?limit=5&offset=5", headers=auth_headers
        )
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_list_saved_searches_sorting(
        self, client, auth_headers, sample_search_params
    ):
        """Test sorting of saved searches"""
        # Create searches with different names
        names = ["Zebra", "Apple", "Mango"]
        for name in names:
            client.post(
                "/api/v1/saved-searches",
                json={"name": name, "search_parameters": sample_search_params},
                headers=auth_headers,
            )

        # Sort by name
        response = client.get(
            "/api/v1/saved-searches?sort_by=name", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert [s["name"] for s in data] == ["Apple", "Mango", "Zebra"]

    def test_get_saved_search(self, client, auth_headers, sample_search_params):
        """Test GET /api/v1/saved-searches/{id}"""
        # Create a search
        create_response = client.post(
            "/api/v1/saved-searches",
            json={
                "name": "Test Search",
                "description": "Test description",
                "search_parameters": sample_search_params,
            },
            headers=auth_headers,
        )
        search_id = create_response.json()["id"]

        # Get the search
        response = client.get(
            f"/api/v1/saved-searches/{search_id}", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == search_id
        assert data["name"] == "Test Search"
        assert data["description"] == "Test description"

    def test_get_saved_search_not_found(self, client, auth_headers):
        """Test getting non-existent search"""
        import uuid

        # Use a valid UUID format that doesn't exist
        nonexistent_id = str(uuid.uuid4())
        response = client.get(
            f"/api/v1/saved-searches/{nonexistent_id}", headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_saved_search(self, client, auth_headers, sample_search_params):
        """Test PUT /api/v1/saved-searches/{id}"""
        # Create a search
        create_response = client.post(
            "/api/v1/saved-searches",
            json={"name": "Original", "search_parameters": sample_search_params},
            headers=auth_headers,
        )
        search_id = create_response.json()["id"]

        # Update it
        new_params = {"search": "capacitor"}
        response = client.put(
            f"/api/v1/saved-searches/{search_id}",
            json={
                "name": "Updated",
                "description": "Updated description",
                "search_parameters": new_params,
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["description"] == "Updated description"
        assert data["search_parameters"] == new_params

    def test_update_saved_search_partial(
        self, client, auth_headers, sample_search_params
    ):
        """Test partial update of saved search"""
        # Create a search
        create_response = client.post(
            "/api/v1/saved-searches",
            json={
                "name": "Original",
                "description": "Original desc",
                "search_parameters": sample_search_params,
            },
            headers=auth_headers,
        )
        search_id = create_response.json()["id"]

        # Update only the name
        response = client.put(
            f"/api/v1/saved-searches/{search_id}",
            json={"name": "New Name"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "Original desc"  # Unchanged
        assert data["search_parameters"] == sample_search_params  # Unchanged

    def test_delete_saved_search(self, client, auth_headers, sample_search_params):
        """Test DELETE /api/v1/saved-searches/{id}"""
        # Create a search
        create_response = client.post(
            "/api/v1/saved-searches",
            json={"name": "To Delete", "search_parameters": sample_search_params},
            headers=auth_headers,
        )
        search_id = create_response.json()["id"]

        # Delete it
        response = client.delete(
            f"/api/v1/saved-searches/{search_id}", headers=auth_headers
        )

        assert response.status_code == 204

        # Verify it's gone
        get_response = client.get(
            f"/api/v1/saved-searches/{search_id}", headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_execute_saved_search(self, client, auth_headers, sample_search_params):
        """Test POST /api/v1/saved-searches/{id}/execute"""
        # Create a search
        create_response = client.post(
            "/api/v1/saved-searches",
            json={"name": "Test Search", "search_parameters": sample_search_params},
            headers=auth_headers,
        )
        search_id = create_response.json()["id"]

        # Execute it
        response = client.post(
            f"/api/v1/saved-searches/{search_id}/execute", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["search_parameters"] == sample_search_params

        # Verify last_used_at was updated
        get_response = client.get(
            f"/api/v1/saved-searches/{search_id}", headers=auth_headers
        )
        assert get_response.json()["last_used_at"] is not None

    def test_duplicate_saved_search(self, client, auth_headers, sample_search_params):
        """Test POST /api/v1/saved-searches/{id}/duplicate"""
        # Create original search
        create_response = client.post(
            "/api/v1/saved-searches",
            json={
                "name": "Original",
                "description": "Original desc",
                "search_parameters": sample_search_params,
            },
            headers=auth_headers,
        )
        original_id = create_response.json()["id"]

        # Duplicate it
        response = client.post(
            f"/api/v1/saved-searches/{original_id}/duplicate",
            json={"name": "Duplicated"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] != original_id
        assert data["name"] == "Duplicated"
        assert data["description"] == "Original desc"
        assert data["search_parameters"] == sample_search_params

    def test_duplicate_saved_search_default_name(
        self, client, auth_headers, sample_search_params
    ):
        """Test duplicating without providing new name"""
        # Create original search
        create_response = client.post(
            "/api/v1/saved-searches",
            json={"name": "Original", "search_parameters": sample_search_params},
            headers=auth_headers,
        )
        original_id = create_response.json()["id"]

        # Duplicate without name
        response = client.post(
            f"/api/v1/saved-searches/{original_id}/duplicate", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Copy of Original"

    def test_get_search_statistics(self, client, auth_headers, sample_search_params):
        """Test GET /api/v1/saved-searches/stats"""
        # Create some searches
        for i in range(5):
            client.post(
                "/api/v1/saved-searches",
                json={
                    "name": f"Search {i}",
                    "search_parameters": sample_search_params,
                },
                headers=auth_headers,
            )

        # Get first two searches and execute them
        list_response = client.get("/api/v1/saved-searches", headers=auth_headers)
        searches = list_response.json()
        for search in searches[:2]:
            client.post(
                f"/api/v1/saved-searches/{search['id']}/execute", headers=auth_headers
            )

        # Get statistics
        response = client.get("/api/v1/saved-searches/stats", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total_searches"] == 5
        assert data["used_searches"] == 2
        assert data["unused_searches"] == 3
        assert data["most_recent_search"] is not None

    def test_user_isolation(
        self, client, auth_headers, sample_search_params, db_session
    ):
        """Test that users can only see their own searches"""
        # Create a search as first user
        create_response = client.post(
            "/api/v1/saved-searches",
            json={"name": "User1 Search", "search_parameters": sample_search_params},
            headers=auth_headers,
        )
        search_id = create_response.json()["id"]

        # Create second user
        user2 = User(username="user2", full_name="User Two")
        user2.set_password("user2pass123")
        db_session.add(user2)
        db_session.commit()

        # Login as second user
        login_response = client.post(
            "/api/v1/auth/token",
            data={"username": "user2", "password": "user2pass123"},
        )
        user2_token = login_response.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # Try to access first user's search
        response = client.get(
            f"/api/v1/saved-searches/{search_id}", headers=user2_headers
        )
        assert response.status_code == 404

        # List searches - should be empty for user2
        list_response = client.get("/api/v1/saved-searches", headers=user2_headers)
        assert len(list_response.json()) == 0
