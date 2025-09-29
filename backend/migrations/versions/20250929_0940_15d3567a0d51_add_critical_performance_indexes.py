"""add_critical_performance_indexes

Revision ID: 15d3567a0d51
Revises: 94401df84656
Create Date: 2025-09-29 09:40:07.326077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15d3567a0d51'
down_revision: Union[str, None] = '94401df84656'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add critical performance indexes for report service optimization."""

    # Helper function to safely create indexes
    def create_index_if_not_exists(connection, index_name, table, columns, unique=False):
        """Create index only if it doesn't already exist."""
        # Check if index exists
        result = connection.execute(
            sa.text("SELECT name FROM sqlite_master WHERE type='index' AND name=:name"),
            {'name': index_name}
        ).fetchone()

        if not result:
            # Create the index using raw SQL for better control
            if isinstance(columns, list) and len(columns) > 1:
                cols_str = ', '.join(columns)
            elif isinstance(columns, list):
                cols_str = columns[0]
            else:
                cols_str = str(columns)

            unique_str = 'UNIQUE ' if unique else ''
            sql = f"CREATE {unique_str}INDEX {index_name} ON {table} ({cols_str})"
            connection.execute(sa.text(sql))
            print(f"Created index: {index_name}")
        else:
            print(f"Index already exists: {index_name}")

    # Get connection
    connection = op.get_bind()

    # ComponentLocation performance indexes - critical for aggregation queries
    create_index_if_not_exists(
        connection,
        'idx_component_locations_component_quantity',
        'component_locations',
        ['component_id', 'quantity_on_hand']
    )

    create_index_if_not_exists(
        connection,
        'idx_component_locations_storage_quantity',
        'component_locations',
        ['storage_location_id', 'quantity_on_hand']
    )

    # Component indexes for financial calculations and category analysis
    create_index_if_not_exists(
        connection,
        'idx_components_category_price',
        'components',
        ['category_id', 'average_purchase_price']
    )

    create_index_if_not_exists(
        connection,
        'idx_components_type_manufacturer',
        'components',
        ['component_type', 'manufacturer']
    )

    # Stock transaction indexes for usage analytics and financial analysis
    create_index_if_not_exists(
        connection,
        'idx_stock_transactions_component_date',
        'stock_transactions',
        ['component_id', 'created_at']
    )

    create_index_if_not_exists(
        connection,
        'idx_stock_transactions_date_type',
        'stock_transactions',
        ['created_at', 'transaction_type']
    )

    create_index_if_not_exists(
        connection,
        'idx_stock_transactions_date_desc',
        'stock_transactions',
        ['created_at DESC']
    )

    # Project component indexes for project analytics
    create_index_if_not_exists(
        connection,
        'idx_project_components_component_allocated',
        'project_components',
        ['component_id', 'quantity_allocated']
    )

    create_index_if_not_exists(
        connection,
        'idx_project_components_project_component',
        'project_components',
        ['project_id', 'component_id']
    )

    # Storage location hierarchy index for location breakdown
    create_index_if_not_exists(
        connection,
        'idx_storage_locations_hierarchy',
        'storage_locations',
        ['location_hierarchy']
    )


def downgrade() -> None:
    """Remove performance indexes."""

    # Drop indexes in reverse order
    op.drop_index('idx_storage_locations_hierarchy', 'storage_locations')
    op.drop_index('idx_project_components_project_component', 'project_components')
    op.drop_index('idx_project_components_component_allocated', 'project_components')
    op.drop_index('idx_stock_transactions_date_desc', 'stock_transactions')
    op.drop_index('idx_stock_transactions_date_type', 'stock_transactions')
    op.drop_index('idx_stock_transactions_component_date', 'stock_transactions')
    op.drop_index('idx_components_type_manufacturer', 'components')
    op.drop_index('idx_components_category_price', 'components')
    op.drop_index('idx_component_locations_storage_quantity', 'component_locations')
    op.drop_index('idx_component_locations_component_quantity', 'component_locations')