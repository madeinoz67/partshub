"""
Unit tests for SavedSearchService
"""

import pytest
from datetime import UTC, datetime

from backend.src.models import SavedSearch, User
from backend.src.services.saved_search_service import SavedSearchService


@pytest.mark.unit
class TestSavedSearchService:
    """Test SavedSearchService CRUD operations"""

    @pytest.fixture
    def test_user(self, db_session):
        """Create a test user"""
        user = User(
            username="testuser",
            full_name="Test User",
            is_active=True,
            is_admin=False,
        )
        user.set_password("testpass123")
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    @pytest.fixture
    def saved_search_service(self, db_session):
        """Create SavedSearchService instance"""
        return SavedSearchService(db_session)

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

    def test_create_saved_search(
        self, saved_search_service, test_user, sample_search_params
    ):
        """Test creating a new saved search"""
        search = saved_search_service.create_saved_search(
            user_id=test_user.id,
            name="Low Stock Resistors",
            search_parameters=sample_search_params,
            description="Find SMD resistors with low stock",
        )

        assert search.id is not None
        assert search.user_id == test_user.id
        assert search.name == "Low Stock Resistors"
        assert search.description == "Find SMD resistors with low stock"
        assert search.search_parameters == sample_search_params
        assert search.created_at is not None
        assert search.updated_at is not None
        assert search.last_used_at is None

    def test_get_saved_search(
        self, saved_search_service, test_user, sample_search_params
    ):
        """Test retrieving a saved search by ID"""
        # Create a search
        created = saved_search_service.create_saved_search(
            user_id=test_user.id,
            name="Test Search",
            search_parameters=sample_search_params,
        )

        # Retrieve it
        retrieved = saved_search_service.get_saved_search(created.id, test_user.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Test Search"
        assert retrieved.search_parameters == sample_search_params

    def test_get_saved_search_wrong_user(
        self, saved_search_service, test_user, sample_search_params, db_session
    ):
        """Test that users cannot access other users' searches"""
        # Create another user
        other_user = User(username="otheruser", full_name="Other User")
        other_user.set_password("otherpass123")
        db_session.add(other_user)
        db_session.commit()

        # Create a search for test_user
        created = saved_search_service.create_saved_search(
            user_id=test_user.id,
            name="Test Search",
            search_parameters=sample_search_params,
        )

        # Try to retrieve with wrong user
        retrieved = saved_search_service.get_saved_search(created.id, other_user.id)

        assert retrieved is None

    def test_list_user_searches(
        self, saved_search_service, test_user, sample_search_params
    ):
        """Test listing all searches for a user"""
        # Create multiple searches
        for i in range(3):
            saved_search_service.create_saved_search(
                user_id=test_user.id,
                name=f"Search {i}",
                search_parameters=sample_search_params,
            )

        # List searches
        searches = saved_search_service.list_user_searches(test_user.id)

        assert len(searches) == 3
        assert all(s.user_id == test_user.id for s in searches)

    def test_list_user_searches_sorting(
        self, saved_search_service, test_user, sample_search_params
    ):
        """Test sorting of user searches"""
        # Create searches with different names
        names = ["Zebra", "Apple", "Mango"]
        for name in names:
            saved_search_service.create_saved_search(
                user_id=test_user.id,
                name=name,
                search_parameters=sample_search_params,
            )

        # Sort by name
        searches = saved_search_service.list_user_searches(
            test_user.id, sort_by="name"
        )

        assert [s.name for s in searches] == ["Apple", "Mango", "Zebra"]

    def test_list_user_searches_pagination(
        self, saved_search_service, test_user, sample_search_params
    ):
        """Test pagination of user searches"""
        # Create 10 searches
        for i in range(10):
            saved_search_service.create_saved_search(
                user_id=test_user.id,
                name=f"Search {i:02d}",
                search_parameters=sample_search_params,
            )

        # Get first page
        page1 = saved_search_service.list_user_searches(
            test_user.id, limit=5, offset=0
        )
        assert len(page1) == 5

        # Get second page
        page2 = saved_search_service.list_user_searches(
            test_user.id, limit=5, offset=5
        )
        assert len(page2) == 5

        # Ensure no overlap
        page1_ids = {s.id for s in page1}
        page2_ids = {s.id for s in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_update_saved_search(
        self, saved_search_service, test_user, sample_search_params
    ):
        """Test updating a saved search"""
        # Create a search
        created = saved_search_service.create_saved_search(
            user_id=test_user.id,
            name="Original Name",
            search_parameters=sample_search_params,
            description="Original description",
        )

        # Update it
        new_params = {"search": "capacitor"}
        updated = saved_search_service.update_saved_search(
            search_id=created.id,
            user_id=test_user.id,
            name="Updated Name",
            description="Updated description",
            search_parameters=new_params,
        )

        assert updated is not None
        assert updated.id == created.id
        assert updated.name == "Updated Name"
        assert updated.description == "Updated description"
        assert updated.search_parameters == new_params

    def test_update_saved_search_partial(
        self, saved_search_service, test_user, sample_search_params
    ):
        """Test partial update of a saved search"""
        # Create a search
        created = saved_search_service.create_saved_search(
            user_id=test_user.id,
            name="Original Name",
            search_parameters=sample_search_params,
        )

        # Update only the name
        updated = saved_search_service.update_saved_search(
            search_id=created.id, user_id=test_user.id, name="New Name"
        )

        assert updated.name == "New Name"
        assert updated.search_parameters == sample_search_params  # Unchanged

    def test_delete_saved_search(
        self, saved_search_service, test_user, sample_search_params
    ):
        """Test deleting a saved search"""
        # Create a search
        created = saved_search_service.create_saved_search(
            user_id=test_user.id,
            name="To Delete",
            search_parameters=sample_search_params,
        )

        # Delete it
        result = saved_search_service.delete_saved_search(created.id, test_user.id)
        assert result is True

        # Verify it's gone
        retrieved = saved_search_service.get_saved_search(created.id, test_user.id)
        assert retrieved is None

    def test_delete_saved_search_wrong_user(
        self, saved_search_service, test_user, sample_search_params, db_session
    ):
        """Test that users cannot delete other users' searches"""
        # Create another user
        other_user = User(username="otheruser", full_name="Other User")
        other_user.set_password("otherpass123")
        db_session.add(other_user)
        db_session.commit()

        # Create a search for test_user
        created = saved_search_service.create_saved_search(
            user_id=test_user.id,
            name="Protected Search",
            search_parameters=sample_search_params,
        )

        # Try to delete with wrong user
        result = saved_search_service.delete_saved_search(created.id, other_user.id)
        assert result is False

        # Verify it still exists
        retrieved = saved_search_service.get_saved_search(created.id, test_user.id)
        assert retrieved is not None

    def test_mark_search_as_used(
        self, saved_search_service, test_user, sample_search_params
    ):
        """Test marking a search as used"""
        # Create a search
        created = saved_search_service.create_saved_search(
            user_id=test_user.id,
            name="Test Search",
            search_parameters=sample_search_params,
        )

        assert created.last_used_at is None

        # Mark as used
        result = saved_search_service.mark_search_as_used(created.id, test_user.id)
        assert result is True

        # Verify last_used_at is set
        retrieved = saved_search_service.get_saved_search(created.id, test_user.id)
        assert retrieved.last_used_at is not None
        assert isinstance(retrieved.last_used_at, datetime)

    def test_get_search_statistics_empty(self, saved_search_service, test_user):
        """Test statistics for user with no searches"""
        stats = saved_search_service.get_search_statistics(test_user.id)

        assert stats["total_searches"] == 0
        assert stats["used_searches"] == 0
        assert stats["unused_searches"] == 0
        assert stats["most_recent_search"] is None

    def test_get_search_statistics(
        self, saved_search_service, test_user, sample_search_params
    ):
        """Test getting search statistics"""
        # Create 5 searches
        for i in range(5):
            saved_search_service.create_saved_search(
                user_id=test_user.id,
                name=f"Search {i}",
                search_parameters=sample_search_params,
            )

        # Mark 2 as used
        searches = saved_search_service.list_user_searches(test_user.id, limit=5)
        saved_search_service.mark_search_as_used(searches[0].id, test_user.id)
        saved_search_service.mark_search_as_used(searches[1].id, test_user.id)

        # Get statistics
        stats = saved_search_service.get_search_statistics(test_user.id)

        assert stats["total_searches"] == 5
        assert stats["used_searches"] == 2
        assert stats["unused_searches"] == 3
        assert stats["most_recent_search"] is not None
        assert stats["most_recent_search"]["id"] in [searches[0].id, searches[1].id]

    def test_duplicate_search(
        self, saved_search_service, test_user, sample_search_params
    ):
        """Test duplicating a saved search"""
        # Create original search
        original = saved_search_service.create_saved_search(
            user_id=test_user.id,
            name="Original Search",
            search_parameters=sample_search_params,
            description="Original description",
        )

        # Duplicate it
        duplicate = saved_search_service.duplicate_search(
            search_id=original.id, user_id=test_user.id, new_name="Duplicated Search"
        )

        assert duplicate is not None
        assert duplicate.id != original.id
        assert duplicate.name == "Duplicated Search"
        assert duplicate.description == original.description
        assert duplicate.search_parameters == original.search_parameters
        assert duplicate.user_id == test_user.id

    def test_duplicate_search_default_name(
        self, saved_search_service, test_user, sample_search_params
    ):
        """Test duplicating with default name"""
        # Create original search
        original = saved_search_service.create_saved_search(
            user_id=test_user.id,
            name="Original Search",
            search_parameters=sample_search_params,
        )

        # Duplicate without providing new name
        duplicate = saved_search_service.duplicate_search(
            search_id=original.id, user_id=test_user.id
        )

        assert duplicate.name == "Copy of Original Search"
