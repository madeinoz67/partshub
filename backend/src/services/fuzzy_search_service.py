"""
Fuzzy search service for manufacturer and footprint autocomplete.

Provides ranked search results using exact matching, prefix matching,
and fuzzy string matching with the rapidfuzz library.
"""

import logging

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from ..models.component import Component

logger = logging.getLogger(__name__)


class FuzzySearchService:
    """
    Service for fuzzy searching manufacturers and footprints.

    Uses a multi-tier ranking algorithm:
    1. Exact match (case-insensitive): score=100
    2. Prefix match (starts with query): score=90
    3. Fuzzy match (rapidfuzz similarity): score=0-100

    Results are sorted by score descending and deduplicated.
    """

    @staticmethod
    async def search_manufacturers(
        db: Session, query: str, limit: int = 10
    ) -> list[dict]:
        """
        Search for manufacturers using fuzzy matching.

        Args:
            db: Database session
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of dictionaries:
            [
                {
                    "id": null,  # No manufacturer table, using component.manufacturer string
                    "name": "Texas Instruments",
                    "score": 100
                }
            ]

        Note: Since there's no separate manufacturer table, we extract unique
        manufacturer names from the components table.
        """
        if not query or not query.strip():
            return []

        query_lower = query.strip().lower()

        # Get all unique manufacturers from components
        manufacturers = (
            db.query(Component.manufacturer)
            .filter(Component.manufacturer.isnot(None))
            .filter(Component.manufacturer != "")
            .distinct()
            .all()
        )

        # Extract manufacturer names
        manufacturer_names = [m[0] for m in manufacturers if m[0]]

        # Score and rank manufacturers
        scored_results = []
        for name in manufacturer_names:
            name_lower = name.lower()

            # Calculate score using ranking algorithm
            if name_lower == query_lower:
                # Exact match
                score = 100
            elif name_lower.startswith(query_lower):
                # Prefix match
                score = 90
            else:
                # Fuzzy match using rapidfuzz
                score = fuzz.ratio(query_lower, name_lower)

            # Only include if score is above threshold
            if score >= 50:  # Minimum relevance threshold
                scored_results.append({"id": None, "name": name, "score": score})

        # Sort by score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        # Deduplicate (shouldn't be necessary, but defensive)
        seen_names = set()
        unique_results = []
        for result in scored_results:
            name_lower = result["name"].lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                unique_results.append(result)

        # Apply limit
        return unique_results[:limit]

    @staticmethod
    async def search_footprints(db: Session, query: str, limit: int = 10) -> list[dict]:
        """
        Search for footprints using fuzzy matching.

        Args:
            db: Database session
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of dictionaries:
            [
                {
                    "id": null,  # No footprint table, using component.package string
                    "name": "0805",
                    "score": 100
                }
            ]

        Note: Since there's no separate footprint table, we extract unique
        package names from the components table.
        """
        if not query or not query.strip():
            return []

        query_lower = query.strip().lower()

        # Get all unique packages (footprints) from components
        packages = (
            db.query(Component.package)
            .filter(Component.package.isnot(None))
            .filter(Component.package != "")
            .distinct()
            .all()
        )

        # Extract package names
        package_names = [p[0] for p in packages if p[0]]

        # Score and rank packages
        scored_results = []
        for name in package_names:
            name_lower = name.lower()

            # Calculate score using ranking algorithm
            if name_lower == query_lower:
                # Exact match
                score = 100
            elif name_lower.startswith(query_lower):
                # Prefix match
                score = 90
            else:
                # Fuzzy match using rapidfuzz
                score = fuzz.ratio(query_lower, name_lower)

            # Only include if score is above threshold
            if score >= 50:  # Minimum relevance threshold
                scored_results.append({"id": None, "name": name, "score": score})

        # Sort by score descending
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        # Deduplicate
        seen_names = set()
        unique_results = []
        for result in scored_results:
            name_lower = result["name"].lower()
            if name_lower not in seen_names:
                seen_names.add(name_lower)
                unique_results.append(result)

        # Apply limit
        return unique_results[:limit]
