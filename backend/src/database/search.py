"""
SQLite FTS5 full-text search configuration for component search optimization.
Enables fast search across component names, part numbers, manufacturers, and notes.
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_session

logger = logging.getLogger(__name__)


class ComponentSearchService:
    """Full-text search service using SQLite FTS5 for fast component discovery."""

    def __init__(self):
        self.fts_table = "components_fts"

    def _ensure_fts_table(self, session: Session | None = None):
        """Create FTS5 virtual table if it doesn't exist."""
        close_session = False
        if session is None:
            session = get_session()
            close_session = True

        try:
            # Check if table exists by trying to query it
            session.execute(text(f"SELECT 1 FROM {self.fts_table} LIMIT 1"))
            # Table exists, we're done
            return
        except Exception:
            # Table doesn't exist, create it
            pass

        try:
            # Create FTS5 virtual table for components
            create_fts_sql = f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {self.fts_table} USING fts5(
                id UNINDEXED,
                name,
                part_number,
                manufacturer,
                component_type,
                value,
                package,
                notes,
                specifications_text,
                tokenize = 'unicode61 remove_diacritics 2'
            )
            """
            session.execute(text(create_fts_sql))

            # Create trigger to automatically update FTS table when components change
            self._create_fts_triggers(session)

            # Only commit if we created the session
            if close_session:
                session.commit()
            else:
                # Flush but don't commit - let caller handle commits
                session.flush()

            logger.info(f"FTS5 table '{self.fts_table}' initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing FTS5 table: {e}")
            session.rollback()
            raise
        finally:
            if close_session:
                session.close()

    def _create_fts_triggers(self, session: Session):
        """Create triggers to keep FTS table in sync with components table."""

        # Drop existing triggers if they exist
        trigger_names = ["components_ai", "components_ad", "components_au"]
        for trigger_name in trigger_names:
            session.execute(text(f"DROP TRIGGER IF EXISTS {trigger_name}"))

        # Trigger for INSERT
        # Convert JSON specifications to searchable text (key: value pairs)
        insert_trigger = f"""
        CREATE TRIGGER components_ai AFTER INSERT ON components BEGIN
            INSERT INTO {self.fts_table}(
                id, name, part_number, manufacturer, component_type,
                value, package, notes, specifications_text
            ) VALUES (
                new.id,
                new.name,
                new.part_number,
                new.manufacturer,
                new.component_type,
                new.value,
                new.package,
                new.notes,
                REPLACE(REPLACE(COALESCE(new.specifications, '{{}}'), '"', ''), ',', ' ')
            );
        END
        """

        # Trigger for DELETE
        delete_trigger = f"""
        CREATE TRIGGER components_ad AFTER DELETE ON components BEGIN
            DELETE FROM {self.fts_table} WHERE id = old.id;
        END
        """

        # Trigger for UPDATE
        # Convert JSON specifications to searchable text (key: value pairs)
        update_trigger = f"""
        CREATE TRIGGER components_au AFTER UPDATE ON components BEGIN
            DELETE FROM {self.fts_table} WHERE id = old.id;
            INSERT INTO {self.fts_table}(
                id, name, part_number, manufacturer, component_type,
                value, package, notes, specifications_text
            ) VALUES (
                new.id,
                new.name,
                new.part_number,
                new.manufacturer,
                new.component_type,
                new.value,
                new.package,
                new.notes,
                REPLACE(REPLACE(COALESCE(new.specifications, '{{}}'), '"', ''), ',', ' ')
            );
        END
        """

        session.execute(text(insert_trigger))
        session.execute(text(delete_trigger))
        session.execute(text(update_trigger))

    def rebuild_fts_index(self, session: Session | None = None):
        """Rebuild the full-text search index from current components data."""
        close_session = False
        if session is None:
            session = get_session()
            close_session = True

        try:
            self._ensure_fts_table(session)
            # Clear existing FTS data
            session.execute(text(f"DELETE FROM {self.fts_table}"))

            # Repopulate from components table
            # Convert JSON specifications to searchable text (key: value pairs)
            populate_sql = f"""
            INSERT INTO {self.fts_table}(
                id, name, part_number, manufacturer, component_type,
                value, package, notes, specifications_text
            )
            SELECT
                id, name, part_number, manufacturer, component_type,
                value, package, notes,
                REPLACE(REPLACE(COALESCE(specifications, '{{}}'), '"', ''), ',', ' ')
            FROM components
            """
            session.execute(text(populate_sql))
            session.commit()

            # Get count for verification
            count_result = session.execute(
                text(f"SELECT COUNT(*) FROM {self.fts_table}")
            ).fetchone()
            count = count_result[0] if count_result else 0

            logger.info(f"FTS index rebuilt with {count} components")
            return count

        except Exception as e:
            logger.error(f"Error rebuilding FTS index: {e}")
            session.rollback()
            raise
        finally:
            if close_session:
                session.close()

    def search_components(
        self,
        query: str,
        session: Session | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[str]:
        """
        Search components using FTS5 and return matching component IDs.

        Args:
            query: Search query (supports FTS5 query syntax)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of component IDs matching the search query
        """
        if not query or not query.strip():
            return []

        close_session = False
        if session is None:
            session = get_session()
            close_session = True

        try:
            self._ensure_fts_table(session)
            # Escape special FTS characters and prepare query
            escaped_query = self._escape_fts_query(query.strip())

            search_sql = f"""
            SELECT id, rank
            FROM {self.fts_table}
            WHERE {self.fts_table} MATCH :query
            ORDER BY rank
            LIMIT :limit OFFSET :offset
            """

            result = session.execute(
                text(search_sql),
                {"query": escaped_query, "limit": limit, "offset": offset},
            )
            component_ids = [row[0] for row in result.fetchall()]

            logger.debug(
                f"FTS search for '{query}' returned {len(component_ids)} results"
            )
            return component_ids

        except Exception as e:
            logger.error(f"Error in FTS search: {e}")
            return []
        finally:
            if close_session:
                session.close()

    def _escape_fts_query(self, query: str) -> str:
        """
        Escape special FTS5 characters and prepare query for search.

        Args:
            query: Raw search query

        Returns:
            Escaped and formatted FTS5 query
        """
        # Remove or escape special FTS5 characters
        special_chars = ['"', "(", ")", "*", ":", "^", "-"]
        escaped_query = query

        for char in special_chars:
            escaped_query = escaped_query.replace(char, " ")

        # Split into terms and join with OR for broader matching
        terms = [term.strip() for term in escaped_query.split() if term.strip()]

        if not terms:
            return '""'  # Empty query that returns no results

        # Create phrase search for multi-word queries or OR search for single words
        if len(terms) == 1:
            return f'"{terms[0]}"*'  # Prefix search for single term
        else:
            # Create OR query for multiple terms
            or_terms = [f'"{term}"*' for term in terms]
            return " OR ".join(or_terms)

    def hybrid_search_components(
        self,
        query: str,
        session: Session | None = None,
        limit: int = 50,
        offset: int = 0,
        fuzzy_threshold: int = 5,
    ) -> list[str]:
        """
        Hybrid search combining FTS5 and rapidfuzz for better results.

        Strategy:
        1. First use FTS5 for fast exact/prefix matching
        2. If FTS5 returns fewer than fuzzy_threshold results, supplement with rapidfuzz
        3. Deduplicate and rank combined results

        Args:
            query: Search query
            session: Database session
            limit: Maximum results to return
            offset: Number of results to skip
            fuzzy_threshold: Min FTS5 results before adding fuzzy matches

        Returns:
            List of component IDs ranked by relevance
        """
        if not query or not query.strip():
            return []

        from rapidfuzz import fuzz

        close_session = False
        if session is None:
            session = get_session()
            close_session = True

        try:
            # Step 1: Get FTS5 results
            fts_results = self.search_components(
                query, session, limit=limit * 2, offset=0
            )

            # Step 2: If we have enough FTS results, just return them
            if len(fts_results) >= fuzzy_threshold:
                logger.debug(
                    f"Hybrid search: FTS5 returned {len(fts_results)} results, "
                    f"skipping fuzzy matching"
                )
                return fts_results[offset : offset + limit]

            # Step 3: FTS results are limited, add fuzzy matching
            logger.debug(
                f"Hybrid search: FTS5 returned {len(fts_results)} results, "
                f"adding fuzzy matching"
            )

            # Get all components for fuzzy matching
            # Only fetch id, name, part_number, manufacturer for scoring
            from ..models.component import Component

            all_components_query = session.query(
                Component.id,
                Component.name,
                Component.part_number,
                Component.manufacturer,
                Component.manufacturer_part_number,
            ).all()

            # Score each component with rapidfuzz
            query_lower = query.strip().lower()
            scored_components = []

            for (
                comp_id,
                name,
                part_num,
                manufacturer,
                manuf_part,
            ) in all_components_query:
                # Build searchable text from available fields
                searchable_fields = [
                    name or "",
                    part_num or "",
                    manufacturer or "",
                    manuf_part or "",
                ]
                combined_text = " ".join(searchable_fields).lower()

                # Calculate fuzzy score
                if not combined_text.strip():
                    continue

                # Use token_set_ratio for better partial matching
                score = fuzz.token_set_ratio(query_lower, combined_text)

                # Only include if score is above threshold (50%)
                if score >= 50:
                    # Boost score if already in FTS results (exact/prefix match)
                    if comp_id in fts_results:
                        score += 20  # Boost FTS matches

                    scored_components.append((comp_id, score))

            # Sort by score descending
            scored_components.sort(key=lambda x: x[1], reverse=True)

            # Extract IDs and deduplicate (maintain order)
            seen_ids = set()
            final_results = []
            for comp_id, score in scored_components:
                if comp_id not in seen_ids:
                    seen_ids.add(comp_id)
                    final_results.append(comp_id)

            logger.debug(
                f"Hybrid search: Combined {len(fts_results)} FTS + fuzzy = "
                f"{len(final_results)} total results"
            )

            # Apply pagination
            return final_results[offset : offset + limit]

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            # Fallback to FTS-only results
            return fts_results[offset : offset + limit] if fts_results else []
        finally:
            if close_session:
                session.close()

    def get_fts_statistics(self, session: Session | None = None) -> dict:
        """Get statistics about the FTS index."""
        close_session = False
        if session is None:
            session = get_session()
            close_session = True

        try:
            self._ensure_fts_table(session)
            # Get FTS table info
            stats_sql = f"""
            SELECT
                (SELECT COUNT(*) FROM {self.fts_table}) as indexed_components,
                (SELECT COUNT(*) FROM components) as total_components
            """
            result = session.execute(text(stats_sql)).fetchone()

            if result:
                indexed_count, total_count = result
                return {
                    "indexed_components": indexed_count,
                    "total_components": total_count,
                    "index_coverage": f"{(indexed_count/total_count*100):.1f}%"
                    if total_count > 0
                    else "0%",
                    "fts_enabled": True,
                }
            else:
                return {
                    "indexed_components": 0,
                    "total_components": 0,
                    "index_coverage": "0%",
                    "fts_enabled": False,
                }

        except Exception as e:
            logger.error(f"Error getting FTS statistics: {e}")
            return {
                "indexed_components": 0,
                "total_components": 0,
                "index_coverage": "0%",
                "fts_enabled": False,
                "error": str(e),
            }
        finally:
            if close_session:
                session.close()


# Global instance - lazy initialized
_component_search_service: ComponentSearchService | None = None


def get_component_search_service() -> ComponentSearchService:
    """Get or create the component search service instance."""
    global _component_search_service
    if _component_search_service is None:
        _component_search_service = ComponentSearchService()
    return _component_search_service


def initialize_component_search():
    """Initialize component search on application startup."""
    try:
        service = get_component_search_service()
        service.rebuild_fts_index()
        logger.info("Component search service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize component search service: {e}")


def search_components_fts(
    query: str, session: Session | None = None, limit: int = 50, offset: int = 0
) -> list[str]:
    """
    Convenience function for FTS component search.

    Args:
        query: Search query
        session: Database session to use (creates new one if None)
        limit: Maximum results
        offset: Results offset

    Returns:
        List of component IDs
    """
    return get_component_search_service().search_components(
        query, session, limit, offset
    )


def hybrid_search_components(
    query: str,
    session: Session | None = None,
    limit: int = 50,
    offset: int = 0,
    fuzzy_threshold: int = 5,
) -> list[str]:
    """
    Hybrid search combining FTS5 and rapidfuzz for better results.

    First attempts FTS5 for fast exact/prefix matching. If fewer than fuzzy_threshold
    results are found, supplements with rapidfuzz fuzzy matching for better recall
    on misspellings and partial matches.

    Args:
        query: Search query
        session: Database session to use (creates new one if None)
        limit: Maximum results
        offset: Results offset
        fuzzy_threshold: Minimum FTS5 results before adding fuzzy matches (default: 5)

    Returns:
        List of component IDs, deduplicated and ranked by relevance
    """
    return get_component_search_service().hybrid_search_components(
        query, session, limit, offset, fuzzy_threshold
    )
