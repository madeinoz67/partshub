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
        self._ensure_fts_table()

    def _ensure_fts_table(self):
        """Create FTS5 virtual table if it doesn't exist."""
        session = get_session()
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

            session.commit()
            logger.info(f"FTS5 table '{self.fts_table}' initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing FTS5 table: {e}")
            session.rollback()
            raise
        finally:
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

    def rebuild_fts_index(self):
        """Rebuild the full-text search index from current components data."""
        session = get_session()
        try:
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
            session.close()

    def search_components(
        self, query: str, limit: int = 50, offset: int = 0
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

        session = get_session()
        try:
            # Escape special FTS characters and prepare query
            escaped_query = self._escape_fts_query(query.strip())

            search_sql = f"""
            SELECT id, rank
            FROM {self.fts_table}
            WHERE {self.fts_table} MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
            """

            result = session.execute(text(search_sql), (escaped_query, limit, offset))
            component_ids = [row[0] for row in result.fetchall()]

            logger.debug(
                f"FTS search for '{query}' returned {len(component_ids)} results"
            )
            return component_ids

        except Exception as e:
            logger.error(f"Error in FTS search: {e}")
            return []
        finally:
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

    def get_fts_statistics(self) -> dict:
        """Get statistics about the FTS index."""
        session = get_session()
        try:
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
            session.close()


# Global instance
component_search_service = ComponentSearchService()


def initialize_component_search():
    """Initialize component search on application startup."""
    try:
        component_search_service.rebuild_fts_index()
        logger.info("Component search service initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize component search service: {e}")


def search_components_fts(query: str, limit: int = 50, offset: int = 0) -> list[str]:
    """
    Convenience function for FTS component search.

    Args:
        query: Search query
        limit: Maximum results
        offset: Results offset

    Returns:
        List of component IDs
    """
    return component_search_service.search_components(query, limit, offset)
