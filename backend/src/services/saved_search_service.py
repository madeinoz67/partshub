"""
SavedSearchService for managing user's saved component search queries.
"""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from ..models import SavedSearch

logger = logging.getLogger(__name__)


class SavedSearchService:
    """Service for managing saved search queries."""

    def __init__(self, db: Session):
        self.db = db

    def create_saved_search(
        self,
        user_id: str,
        name: str,
        search_parameters: dict[str, Any],
        description: str | None = None,
    ) -> SavedSearch:
        """
        Create a new saved search for a user.

        Args:
            user_id: ID of the user creating the search
            name: Name of the saved search
            search_parameters: Dictionary of search criteria
            description: Optional description

        Returns:
            Created SavedSearch instance
        """
        saved_search = SavedSearch(
            user_id=user_id,
            name=name,
            description=description,
            search_parameters=search_parameters,
        )

        self.db.add(saved_search)
        self.db.commit()
        self.db.refresh(saved_search)

        logger.info(f"Created saved search '{name}' for user {user_id}")
        return saved_search

    def get_saved_search(self, search_id: str, user_id: str) -> SavedSearch | None:
        """
        Get a specific saved search by ID.

        Args:
            search_id: ID of the saved search
            user_id: ID of the user (for ownership verification)

        Returns:
            SavedSearch instance or None if not found/not owned by user
        """
        return (
            self.db.query(SavedSearch)
            .filter(SavedSearch.id == search_id, SavedSearch.user_id == user_id)
            .first()
        )

    def list_user_searches(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "updated_at",
    ) -> list[SavedSearch]:
        """
        List all saved searches for a user.

        Args:
            user_id: ID of the user
            limit: Maximum number of results
            offset: Number of results to skip
            sort_by: Field to sort by (created_at, updated_at, last_used_at, name)

        Returns:
            List of SavedSearch instances
        """
        query = self.db.query(SavedSearch).filter(SavedSearch.user_id == user_id)

        # Apply sorting
        if sort_by == "name":
            query = query.order_by(SavedSearch.name)
        elif sort_by == "created_at":
            query = query.order_by(desc(SavedSearch.created_at))
        elif sort_by == "last_used_at":
            query = query.order_by(
                desc(SavedSearch.last_used_at.is_(None)),
                desc(SavedSearch.last_used_at),
            )
        else:  # default to updated_at
            query = query.order_by(desc(SavedSearch.updated_at))

        return query.offset(offset).limit(limit).all()

    def update_saved_search(
        self,
        search_id: str,
        user_id: str,
        name: str | None = None,
        description: str | None = None,
        search_parameters: dict[str, Any] | None = None,
    ) -> SavedSearch | None:
        """
        Update an existing saved search.

        Args:
            search_id: ID of the saved search
            user_id: ID of the user (for ownership verification)
            name: New name (optional)
            description: New description (optional)
            search_parameters: New search parameters (optional)

        Returns:
            Updated SavedSearch instance or None if not found/not owned
        """
        saved_search = self.get_saved_search(search_id, user_id)
        if not saved_search:
            return None

        if name is not None:
            saved_search.name = name
        if description is not None:
            saved_search.description = description
        if search_parameters is not None:
            saved_search.search_parameters = search_parameters

        saved_search.updated_at = datetime.now(UTC)
        self.db.commit()
        self.db.refresh(saved_search)

        logger.info(f"Updated saved search {search_id} for user {user_id}")
        return saved_search

    def delete_saved_search(self, search_id: str, user_id: str) -> bool:
        """
        Delete a saved search.

        Args:
            search_id: ID of the saved search
            user_id: ID of the user (for ownership verification)

        Returns:
            True if deleted, False if not found/not owned
        """
        saved_search = self.get_saved_search(search_id, user_id)
        if not saved_search:
            return False

        self.db.delete(saved_search)
        self.db.commit()

        logger.info(f"Deleted saved search {search_id} for user {user_id}")
        return True

    def mark_search_as_used(self, search_id: str, user_id: str) -> bool:
        """
        Update the last_used_at timestamp for a saved search.

        Args:
            search_id: ID of the saved search
            user_id: ID of the user (for ownership verification)

        Returns:
            True if updated, False if not found/not owned
        """
        saved_search = self.get_saved_search(search_id, user_id)
        if not saved_search:
            return False

        saved_search.mark_as_used()
        self.db.commit()

        return True

    def get_search_statistics(self, user_id: str) -> dict[str, Any]:
        """
        Get statistics about a user's saved searches.

        Args:
            user_id: ID of the user

        Returns:
            Dictionary with statistics
        """
        searches = self.list_user_searches(user_id, limit=1000)

        # Count searches that have been used at least once
        used_searches = sum(1 for s in searches if s.last_used_at is not None)

        # Find most recently used search
        most_recent = None
        if searches:
            recent_searches = [s for s in searches if s.last_used_at is not None]
            if recent_searches:
                most_recent = max(recent_searches, key=lambda s: s.last_used_at)

        return {
            "total_searches": len(searches),
            "used_searches": used_searches,
            "unused_searches": len(searches) - used_searches,
            "most_recent_search": {
                "id": most_recent.id,
                "name": most_recent.name,
                "last_used_at": most_recent.last_used_at.isoformat(),
            }
            if most_recent
            else None,
        }

    def duplicate_search(
        self, search_id: str, user_id: str, new_name: str | None = None
    ) -> SavedSearch | None:
        """
        Duplicate an existing saved search.

        Args:
            search_id: ID of the saved search to duplicate
            user_id: ID of the user (for ownership verification)
            new_name: Name for the duplicated search (defaults to "Copy of {original_name}")

        Returns:
            New SavedSearch instance or None if original not found/not owned
        """
        original = self.get_saved_search(search_id, user_id)
        if not original:
            return None

        duplicate_name = new_name or f"Copy of {original.name}"

        duplicate = SavedSearch(
            user_id=user_id,
            name=duplicate_name,
            description=original.description,
            search_parameters=original.search_parameters.copy(),
        )

        self.db.add(duplicate)
        self.db.commit()
        self.db.refresh(duplicate)

        logger.info(f"Duplicated saved search {search_id} to {duplicate.id} for user {user_id}")
        return duplicate
