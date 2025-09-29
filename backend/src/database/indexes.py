"""
Database indexing optimization for component search performance.
Creates database indexes to improve query performance for search and filtering operations.
"""

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def create_search_indexes(session: Session) -> None:
    """
    Create database indexes to optimize component search performance.

    This function creates indexes on frequently queried columns to improve
    search performance across components, categories, storage locations, and tags.
    """

    indexes_to_create = [
        # Component search indexes
        "CREATE INDEX IF NOT EXISTS idx_components_name ON components(name)",
        "CREATE INDEX IF NOT EXISTS idx_components_part_number ON components(part_number)",
        "CREATE INDEX IF NOT EXISTS idx_components_manufacturer ON components(manufacturer)",
        "CREATE INDEX IF NOT EXISTS idx_components_component_type ON components(component_type)",
        "CREATE INDEX IF NOT EXISTS idx_components_value ON components(value)",
        "CREATE INDEX IF NOT EXISTS idx_components_package ON components(package)",
        "CREATE INDEX IF NOT EXISTS idx_components_category_id ON components(category_id)",
        # Note: storage_location_id, quantity_on_hand, unit_cost are handled via relationships/properties
        "CREATE INDEX IF NOT EXISTS idx_components_created_at ON components(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_components_updated_at ON components(updated_at)",
        # Composite indexes for common search patterns
        "CREATE INDEX IF NOT EXISTS idx_components_type_manufacturer ON components(component_type, manufacturer)",
        "CREATE INDEX IF NOT EXISTS idx_components_category_name ON components(category_id, name)",
        # Note: location_quantity index removed - handled via ComponentLocation relationship
        # Category indexes
        "CREATE INDEX IF NOT EXISTS idx_categories_name ON categories(name)",
        "CREATE INDEX IF NOT EXISTS idx_categories_parent_id ON categories(parent_id)",
        # Storage location indexes
        "CREATE INDEX IF NOT EXISTS idx_storage_locations_name ON storage_locations(name)",
        # Note: location_type column doesn't exist in current schema
        "CREATE INDEX IF NOT EXISTS idx_storage_locations_parent_id ON storage_locations(parent_id)",
        # Tag indexes for tag-based search
        "CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)",
        "CREATE INDEX IF NOT EXISTS idx_component_tags_component_id ON component_tags(component_id)",
        "CREATE INDEX IF NOT EXISTS idx_component_tags_tag_id ON component_tags(tag_id)",
        # Stock transaction indexes for history queries
        "CREATE INDEX IF NOT EXISTS idx_stock_transactions_component_id ON stock_transactions(component_id)",
        "CREATE INDEX IF NOT EXISTS idx_stock_transactions_created_at ON stock_transactions(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_stock_transactions_transaction_type ON stock_transactions(transaction_type)",
        # Project component allocation indexes
        "CREATE INDEX IF NOT EXISTS idx_project_components_project_id ON project_components(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_project_components_component_id ON project_components(component_id)",
        # Attachment indexes for file operations
        "CREATE INDEX IF NOT EXISTS idx_attachments_component_id ON attachments(component_id)",
        "CREATE INDEX IF NOT EXISTS idx_attachments_attachment_type ON attachments(attachment_type)",
        # Note: is_primary column doesn't exist in current schema
        # Custom field indexes for specification searches
        "CREATE INDEX IF NOT EXISTS idx_custom_field_values_component_id ON custom_field_values(component_id)",
        # Note: custom_field_id column doesn't exist in current schema
        # Purchase tracking indexes
        "CREATE INDEX IF NOT EXISTS idx_purchase_items_component_id ON purchase_items(component_id)",
        "CREATE INDEX IF NOT EXISTS idx_purchases_created_at ON purchases(created_at)",
        # ComponentLocation indexes for multi-location inventory support
        "CREATE INDEX IF NOT EXISTS idx_component_locations_component_id ON component_locations(component_id)",
        "CREATE INDEX IF NOT EXISTS idx_component_locations_storage_location_id ON component_locations(storage_location_id)",
        "CREATE INDEX IF NOT EXISTS idx_component_locations_quantity_on_hand ON component_locations(quantity_on_hand)",
        "CREATE INDEX IF NOT EXISTS idx_component_locations_minimum_stock ON component_locations(minimum_stock)",
        # Composite index for stock status queries
        "CREATE INDEX IF NOT EXISTS idx_component_locations_component_quantity ON component_locations(component_id, quantity_on_hand)",
        # Storage location type index for filtering
        "CREATE INDEX IF NOT EXISTS idx_storage_locations_type ON storage_locations(type)",
        "CREATE INDEX IF NOT EXISTS idx_storage_locations_hierarchy ON storage_locations(location_hierarchy)",
        # KiCad integration indexes
        "CREATE INDEX IF NOT EXISTS idx_kicad_library_data_component_id ON kicad_library_data(component_id)",
        # Note: has_symbol and has_footprint columns don't exist in current schema
        # Provider data indexes
        "CREATE INDEX IF NOT EXISTS idx_component_provider_data_component_id ON component_provider_data(component_id)",
        "CREATE INDEX IF NOT EXISTS idx_component_provider_data_provider_id ON component_provider_data(provider_id)",
    ]

    # FTS5 search optimization indexes
    fts_indexes = [
        # Create FTS5 virtual table if not exists (handled by search.py)
        # But add indexes on the main table for hybrid search approaches
        "CREATE INDEX IF NOT EXISTS idx_components_search_text ON components(name, part_number, manufacturer, notes)",
    ]

    try:
        logger.info("Creating database search optimization indexes...")

        for index_sql in indexes_to_create:
            try:
                session.execute(text(index_sql))
                index_name = (
                    index_sql.split("idx_")[1].split(" ")[0]
                    if "idx_" in index_sql
                    else "unknown"
                )
                logger.debug(f"Created index: idx_{index_name}")
            except Exception as e:
                logger.warning(f"Failed to create index: {index_sql}. Error: {e}")

        # Create FTS indexes
        for fts_sql in fts_indexes:
            try:
                session.execute(text(fts_sql))
                logger.debug(f"Created FTS index: {fts_sql}")
            except Exception as e:
                logger.warning(f"Failed to create FTS index: {fts_sql}. Error: {e}")

        session.commit()
        logger.info(
            f"Successfully created {len(indexes_to_create)} database indexes for search optimization"
        )

    except Exception as e:
        logger.error(f"Error creating search indexes: {e}")
        session.rollback()
        raise


def analyze_search_performance(session: Session) -> dict:
    """
    Analyze search performance by checking query execution plans.

    Returns:
        Dictionary with performance analysis results
    """
    performance_queries = [
        {
            "name": "component_name_search",
            "query": "SELECT * FROM components WHERE name LIKE '%resistor%' LIMIT 10",
            "description": "Component name search performance",
        },
        {
            "name": "component_manufacturer_search",
            "query": "SELECT * FROM components WHERE manufacturer = 'Yageo' LIMIT 10",
            "description": "Manufacturer filtering performance",
        },
        {
            "name": "category_filter",
            "query": "SELECT c.* FROM components c JOIN categories cat ON c.category_id = cat.id WHERE cat.name = 'Resistors' LIMIT 10",
            "description": "Category filtering performance",
        },
        # Note: low_stock_query removed - quantity_on_hand is a computed property, not a column
        {
            "name": "composite_search",
            "query": "SELECT * FROM components WHERE component_type = 'resistor' AND manufacturer = 'Yageo' LIMIT 10",
            "description": "Composite search performance",
        },
    ]

    results = {}

    try:
        for query_info in performance_queries:
            # Get query execution plan
            explain_query = f"EXPLAIN QUERY PLAN {query_info['query']}"

            try:
                result = session.execute(text(explain_query)).fetchall()

                # Check if indexes are being used
                plan_text = " ".join([str(row) for row in result])
                uses_index = (
                    "USING INDEX" in plan_text.upper() or "INDEX" in plan_text.upper()
                )

                results[query_info["name"]] = {
                    "description": query_info["description"],
                    "uses_index": uses_index,
                    "execution_plan": plan_text,
                    "optimized": uses_index,
                }

                logger.debug(f"Query {query_info['name']}: Index usage = {uses_index}")

            except Exception as e:
                results[query_info["name"]] = {
                    "description": query_info["description"],
                    "error": str(e),
                    "optimized": False,
                }
                logger.warning(f"Failed to analyze query {query_info['name']}: {e}")

    except Exception as e:
        logger.error(f"Error analyzing search performance: {e}")

    return results


def drop_search_indexes(session: Session) -> None:
    """
    Drop all search optimization indexes.
    Useful for development or migration scenarios.
    """

    indexes_to_drop = [
        "DROP INDEX IF EXISTS idx_components_name",
        "DROP INDEX IF EXISTS idx_components_part_number",
        "DROP INDEX IF EXISTS idx_components_manufacturer",
        "DROP INDEX IF EXISTS idx_components_component_type",
        "DROP INDEX IF EXISTS idx_components_value",
        "DROP INDEX IF EXISTS idx_components_package",
        "DROP INDEX IF EXISTS idx_components_category_id",
        # Note: storage_location_id, quantity_on_hand, unit_cost indexes removed
        "DROP INDEX IF EXISTS idx_components_created_at",
        "DROP INDEX IF EXISTS idx_components_updated_at",
        "DROP INDEX IF EXISTS idx_components_type_manufacturer",
        "DROP INDEX IF EXISTS idx_components_category_name",
        # Note: location_quantity index removed
        "DROP INDEX IF EXISTS idx_categories_name",
        "DROP INDEX IF EXISTS idx_categories_parent_id",
        "DROP INDEX IF EXISTS idx_storage_locations_name",
        # Note: location_type index removed
        "DROP INDEX IF EXISTS idx_storage_locations_parent_id",
        "DROP INDEX IF EXISTS idx_tags_name",
        "DROP INDEX IF EXISTS idx_component_tags_component_id",
        "DROP INDEX IF EXISTS idx_component_tags_tag_id",
        "DROP INDEX IF EXISTS idx_stock_transactions_component_id",
        "DROP INDEX IF EXISTS idx_stock_transactions_created_at",
        "DROP INDEX IF EXISTS idx_stock_transactions_transaction_type",
        "DROP INDEX IF EXISTS idx_project_components_project_id",
        "DROP INDEX IF EXISTS idx_project_components_component_id",
        "DROP INDEX IF EXISTS idx_attachments_component_id",
        "DROP INDEX IF EXISTS idx_attachments_attachment_type",
        # Note: is_primary index removed
        "DROP INDEX IF EXISTS idx_custom_field_values_component_id",
        # Note: custom_field_id index removed
        "DROP INDEX IF EXISTS idx_purchase_items_component_id",
        "DROP INDEX IF EXISTS idx_purchases_created_at",
        "DROP INDEX IF EXISTS idx_kicad_library_data_component_id",
        # Note: has_symbol and has_footprint indexes removed
        "DROP INDEX IF EXISTS idx_component_provider_data_component_id",
        "DROP INDEX IF EXISTS idx_component_provider_data_provider_id",
        "DROP INDEX IF EXISTS idx_components_search_text",
    ]

    try:
        logger.info("Dropping search optimization indexes...")

        for drop_sql in indexes_to_drop:
            try:
                session.execute(text(drop_sql))
            except Exception as e:
                logger.warning(f"Failed to drop index: {drop_sql}. Error: {e}")

        session.commit()
        logger.info(f"Successfully dropped {len(indexes_to_drop)} database indexes")

    except Exception as e:
        logger.error(f"Error dropping search indexes: {e}")
        session.rollback()
        raise


def get_index_statistics(session: Session) -> dict:
    """
    Get statistics about existing database indexes.

    Returns:
        Dictionary with index statistics and recommendations
    """
    try:
        # Get all indexes
        indexes_query = """
        SELECT name, tbl_name, sql
        FROM sqlite_master
        WHERE type = 'index'
        AND name LIKE 'idx_%'
        ORDER BY tbl_name, name
        """

        indexes = session.execute(text(indexes_query)).fetchall()

        # Get table statistics
        tables_query = """
        SELECT name,
               (SELECT COUNT(*) FROM components) as component_count,
               (SELECT COUNT(*) FROM categories) as category_count,
               (SELECT COUNT(*) FROM storage_locations) as location_count,
               (SELECT COUNT(*) FROM tags) as tag_count
        FROM sqlite_master
        WHERE type = 'table' AND name = 'components'
        """

        table_stats = session.execute(text(tables_query)).fetchone()

        stats = {
            "total_indexes": len(indexes),
            "indexes_by_table": {},
            "table_statistics": {
                "components": table_stats[1] if table_stats else 0,
                "categories": table_stats[2] if table_stats else 0,
                "storage_locations": table_stats[3] if table_stats else 0,
                "tags": table_stats[4] if table_stats else 0,
            },
            "index_list": [],
        }

        for index in indexes:
            table_name = index[1]
            if table_name not in stats["indexes_by_table"]:
                stats["indexes_by_table"][table_name] = 0
            stats["indexes_by_table"][table_name] += 1

            stats["index_list"].append(
                {"name": index[0], "table": index[1], "sql": index[2]}
            )

        return stats

    except Exception as e:
        logger.error(f"Error getting index statistics: {e}")
        return {"error": str(e)}


def optimize_database_for_search(session: Session) -> dict:
    """
    Comprehensive database optimization for search performance.

    This function:
    1. Creates all necessary indexes
    2. Analyzes performance
    3. Returns optimization results
    """

    results = {
        "indexes_created": False,
        "performance_analysis": {},
        "recommendations": [],
        "errors": [],
    }

    try:
        # Create indexes
        create_search_indexes(session)
        results["indexes_created"] = True

        # Analyze performance
        results["performance_analysis"] = analyze_search_performance(session)

        # Generate recommendations
        optimized_queries = sum(
            1
            for q in results["performance_analysis"].values()
            if q.get("optimized", False)
        )
        total_queries = len(results["performance_analysis"])

        if optimized_queries == total_queries:
            results["recommendations"].append(
                "✅ All queries are optimized with indexes"
            )
        else:
            results["recommendations"].append(
                f"⚠️ {total_queries - optimized_queries} queries may need optimization"
            )

        # Check table sizes for additional recommendations
        stats = get_index_statistics(session)
        component_count = stats.get("table_statistics", {}).get("components", 0)

        if component_count > 1000:
            results["recommendations"].append(
                "📊 Large component table detected - indexes are critical for performance"
            )
        if component_count > 10000:
            results["recommendations"].append(
                "🚀 Consider implementing database partitioning for very large datasets"
            )

        results["recommendations"].append(
            f"📈 Database contains {component_count} components with {stats.get('total_indexes', 0)} search indexes"
        )

    except Exception as e:
        error_msg = f"Database optimization failed: {e}"
        results["errors"].append(error_msg)
        logger.error(error_msg)

    return results
