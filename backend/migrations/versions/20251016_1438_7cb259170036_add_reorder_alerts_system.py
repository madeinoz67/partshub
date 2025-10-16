"""add_reorder_alerts_system

Revision ID: 7cb259170036
Revises: 8711dfb3a716
Create Date: 2025-10-16 14:38:28.940861

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7cb259170036'
down_revision: Union[str, None] = '8711dfb3a716'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Extend component_locations table
    # Note: SQLite doesn't support adding constraints via ALTER TABLE
    # The constraint will be enforced at the application layer (service validation)

    # Check if columns already exist (from failed migration attempt)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('component_locations')]

    if 'reorder_threshold' not in columns:
        op.add_column('component_locations',
            sa.Column('reorder_threshold', sa.Integer(), nullable=False, server_default='0'))

    if 'reorder_enabled' not in columns:
        op.add_column('component_locations',
            sa.Column('reorder_enabled', sa.Boolean(), nullable=False, server_default='0'))

    # Add index for efficient low-stock queries (skip if exists)
    indexes = [idx['name'] for idx in inspector.get_indexes('component_locations')]
    if 'idx_component_locations_reorder' not in indexes:
        op.execute("""
            CREATE INDEX idx_component_locations_reorder
            ON component_locations(reorder_enabled, quantity_on_hand, reorder_threshold)
            WHERE reorder_enabled = 1
        """)

    # 2. Create reorder_alerts table
    op.create_table(
        'reorder_alerts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('component_location_id', sa.Integer(), nullable=False),
        sa.Column('component_id', sa.String(), nullable=False),  # UUID stored as String
        sa.Column('storage_location_id', sa.String(), nullable=False),  # UUID stored as String
        sa.Column('status', sa.String(), nullable=False, server_default='active'),
        sa.Column('current_quantity', sa.Integer(), nullable=False),
        sa.Column('reorder_threshold', sa.Integer(), nullable=False),
        sa.Column('shortage_amount', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.String(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.Column('updated_at', sa.String(), nullable=False, server_default=sa.text("(datetime('now'))")),
        sa.Column('dismissed_at', sa.String(), nullable=True),
        sa.Column('ordered_at', sa.String(), nullable=True),
        sa.Column('resolved_at', sa.String(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['component_location_id'], ['component_locations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['component_id'], ['components.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['storage_location_id'], ['storage_locations.id'], ondelete='CASCADE'),
        sa.CheckConstraint("status IN ('active', 'dismissed', 'ordered', 'resolved')", name='ck_reorder_alerts_status')
    )

    # 3. Create indexes
    op.create_index('idx_reorder_alerts_status', 'reorder_alerts', ['status', sa.text('created_at DESC')])
    op.create_index('idx_reorder_alerts_component', 'reorder_alerts', ['component_id', 'status'])
    op.create_index('idx_reorder_alerts_location', 'reorder_alerts', ['storage_location_id', 'status'])
    op.create_index('idx_reorder_alerts_component_location_status', 'reorder_alerts', ['component_location_id', 'status'])

    # Unique constraint: one active alert per component_location
    op.execute("""
        CREATE UNIQUE INDEX idx_reorder_alerts_unique_active
        ON reorder_alerts(component_location_id)
        WHERE status = 'active'
    """)

    # 4. Create SQLite triggers
    # Trigger 1: Create alert when stock drops below threshold (UPDATE case)
    op.execute("""
        CREATE TRIGGER trigger_check_low_stock_after_update
        AFTER UPDATE OF quantity_on_hand ON component_locations
        FOR EACH ROW
        WHEN NEW.reorder_enabled = 1
          AND NEW.quantity_on_hand < NEW.reorder_threshold
          AND OLD.quantity_on_hand >= OLD.reorder_threshold
          AND NOT EXISTS (
            SELECT 1 FROM reorder_alerts
            WHERE component_location_id = NEW.id
              AND status = 'active'
          )
        BEGIN
          INSERT INTO reorder_alerts (
            component_location_id,
            component_id,
            storage_location_id,
            status,
            current_quantity,
            reorder_threshold,
            shortage_amount
          )
          VALUES (
            NEW.id,
            NEW.component_id,
            NEW.storage_location_id,
            'active',
            NEW.quantity_on_hand,
            NEW.reorder_threshold,
            NEW.reorder_threshold - NEW.quantity_on_hand
          );
        END;
    """)

    # Trigger 2: Update existing alert when quantity changes further
    op.execute("""
        CREATE TRIGGER trigger_update_low_stock_after_update
        AFTER UPDATE OF quantity_on_hand ON component_locations
        FOR EACH ROW
        WHEN NEW.reorder_enabled = 1
          AND NEW.quantity_on_hand < NEW.reorder_threshold
          AND EXISTS (
            SELECT 1 FROM reorder_alerts
            WHERE component_location_id = NEW.id
              AND status = 'active'
          )
        BEGIN
          UPDATE reorder_alerts
          SET
            current_quantity = NEW.quantity_on_hand,
            shortage_amount = NEW.reorder_threshold - NEW.quantity_on_hand,
            updated_at = datetime('now')
          WHERE component_location_id = NEW.id
            AND status = 'active';
        END;
    """)

    # Trigger 3: Auto-resolve alert when stock rises above threshold
    op.execute("""
        CREATE TRIGGER trigger_resolve_alert_after_update
        AFTER UPDATE OF quantity_on_hand ON component_locations
        FOR EACH ROW
        WHEN NEW.quantity_on_hand >= NEW.reorder_threshold
          AND OLD.quantity_on_hand < OLD.reorder_threshold
        BEGIN
          UPDATE reorder_alerts
          SET
            status = 'resolved',
            resolved_at = datetime('now'),
            updated_at = datetime('now')
          WHERE component_location_id = NEW.id
            AND status IN ('active', 'ordered');
        END;
    """)

    # Trigger 4: Create alert on initial stock entry (INSERT case)
    op.execute("""
        CREATE TRIGGER trigger_check_low_stock_after_insert
        AFTER INSERT ON component_locations
        FOR EACH ROW
        WHEN NEW.reorder_enabled = 1
          AND NEW.quantity_on_hand < NEW.reorder_threshold
        BEGIN
          INSERT INTO reorder_alerts (
            component_location_id,
            component_id,
            storage_location_id,
            status,
            current_quantity,
            reorder_threshold,
            shortage_amount
          )
          VALUES (
            NEW.id,
            NEW.component_id,
            NEW.storage_location_id,
            'active',
            NEW.quantity_on_hand,
            NEW.reorder_threshold,
            NEW.reorder_threshold - NEW.quantity_on_hand
          );
        END;
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_check_low_stock_after_insert")
    op.execute("DROP TRIGGER IF EXISTS trigger_resolve_alert_after_update")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_low_stock_after_update")
    op.execute("DROP TRIGGER IF EXISTS trigger_check_low_stock_after_update")

    # Drop reorder_alerts table (cascades to indexes)
    op.drop_table('reorder_alerts')

    # Drop component_locations indexes and columns
    op.execute("DROP INDEX IF EXISTS idx_component_locations_reorder")
    op.drop_column('component_locations', 'reorder_enabled')
    op.drop_column('component_locations', 'reorder_threshold')
