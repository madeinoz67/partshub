"""add_critical_performance_indexes

Revision ID: f3306731c2f3
Revises: 587c37774a38
Create Date: 2025-09-30 21:04:29.573829

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f3306731c2f3'
down_revision: Union[str, None] = '587c37774a38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add critical performance indexes for report service optimization."""
    # Get database connection to check table and index existence
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    def index_exists(table_name: str, index_name: str) -> bool:
        """Check if an index exists on a table."""
        indexes = inspector.get_indexes(table_name)
        return any(idx['name'] == index_name for idx in indexes)

    # 1. idx_component_locations_component_quantity - for aggregation queries
    if 'component_locations' in existing_tables and not index_exists('component_locations', 'idx_component_locations_component_quantity'):
        op.create_index(
            'idx_component_locations_component_quantity',
            'component_locations',
            ['component_id', 'quantity_on_hand'],
            unique=False
        )

    # 2. idx_component_locations_storage_quantity - for aggregation queries
    if 'component_locations' in existing_tables and not index_exists('component_locations', 'idx_component_locations_storage_quantity'):
        op.create_index(
            'idx_component_locations_storage_quantity',
            'component_locations',
            ['storage_location_id', 'quantity_on_hand'],
            unique=False
        )

    # 3. idx_components_category_price - for financial calculations
    if 'components' in existing_tables and not index_exists('components', 'idx_components_category_price'):
        op.create_index(
            'idx_components_category_price',
            'components',
            ['category_id', 'average_purchase_price'],
            unique=False
        )

    # 4. idx_components_type_manufacturer - for category analysis
    if 'components' in existing_tables and not index_exists('components', 'idx_components_type_manufacturer'):
        op.create_index(
            'idx_components_type_manufacturer',
            'components',
            ['component_type', 'manufacturer'],
            unique=False
        )

    # 5. idx_stock_transactions_component_date - for usage analytics
    if 'stock_transactions' in existing_tables and not index_exists('stock_transactions', 'idx_stock_transactions_component_date'):
        op.create_index(
            'idx_stock_transactions_component_date',
            'stock_transactions',
            ['component_id', 'created_at'],
            unique=False
        )

    # 6. idx_stock_transactions_date_type - for financial analysis
    if 'stock_transactions' in existing_tables and not index_exists('stock_transactions', 'idx_stock_transactions_date_type'):
        op.create_index(
            'idx_stock_transactions_date_type',
            'stock_transactions',
            ['created_at', 'transaction_type'],
            unique=False
        )

    # 7. idx_stock_transactions_date_desc - for recent transactions
    if 'stock_transactions' in existing_tables and not index_exists('stock_transactions', 'idx_stock_transactions_date_desc'):
        op.create_index(
            'idx_stock_transactions_date_desc',
            'stock_transactions',
            [sa.text('created_at DESC')],
            unique=False
        )

    # 8. idx_project_components_component_allocated - for project analytics
    if 'project_components' in existing_tables and not index_exists('project_components', 'idx_project_components_component_allocated'):
        op.create_index(
            'idx_project_components_component_allocated',
            'project_components',
            ['component_id', 'quantity_allocated'],
            unique=False
        )

    # 9. idx_project_components_project_component - for project queries
    if 'project_components' in existing_tables and not index_exists('project_components', 'idx_project_components_project_component'):
        op.create_index(
            'idx_project_components_project_component',
            'project_components',
            ['project_id', 'component_id'],
            unique=False
        )

    # 10. idx_storage_locations_hierarchy - for location breakdown
    if 'storage_locations' in existing_tables and not index_exists('storage_locations', 'idx_storage_locations_hierarchy'):
        op.create_index(
            'idx_storage_locations_hierarchy',
            'storage_locations',
            ['location_hierarchy'],
            unique=False
        )


def downgrade() -> None:
    """Remove critical performance indexes."""
    # Get database connection to check table and index existence
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    existing_tables = inspector.get_table_names()

    def index_exists(table_name: str, index_name: str) -> bool:
        """Check if an index exists on a table."""
        indexes = inspector.get_indexes(table_name)
        return any(idx['name'] == index_name for idx in indexes)

    # Drop indexes in reverse order
    if 'storage_locations' in existing_tables and index_exists('storage_locations', 'idx_storage_locations_hierarchy'):
        op.drop_index('idx_storage_locations_hierarchy', table_name='storage_locations')

    if 'project_components' in existing_tables:
        if index_exists('project_components', 'idx_project_components_project_component'):
            op.drop_index('idx_project_components_project_component', table_name='project_components')
        if index_exists('project_components', 'idx_project_components_component_allocated'):
            op.drop_index('idx_project_components_component_allocated', table_name='project_components')

    if 'stock_transactions' in existing_tables:
        if index_exists('stock_transactions', 'idx_stock_transactions_date_desc'):
            op.drop_index('idx_stock_transactions_date_desc', table_name='stock_transactions')
        if index_exists('stock_transactions', 'idx_stock_transactions_date_type'):
            op.drop_index('idx_stock_transactions_date_type', table_name='stock_transactions')
        if index_exists('stock_transactions', 'idx_stock_transactions_component_date'):
            op.drop_index('idx_stock_transactions_component_date', table_name='stock_transactions')

    if 'components' in existing_tables:
        if index_exists('components', 'idx_components_type_manufacturer'):
            op.drop_index('idx_components_type_manufacturer', table_name='components')
        if index_exists('components', 'idx_components_category_price'):
            op.drop_index('idx_components_category_price', table_name='components')

    if 'component_locations' in existing_tables:
        if index_exists('component_locations', 'idx_component_locations_storage_quantity'):
            op.drop_index('idx_component_locations_storage_quantity', table_name='component_locations')
        if index_exists('component_locations', 'idx_component_locations_component_quantity'):
            op.drop_index('idx_component_locations_component_quantity', table_name='component_locations')