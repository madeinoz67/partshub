"""Add provider integration models

Revision ID: c2d2d7527a07
Revises: d8c3096b71a6
Create Date: 2025-09-26 11:54:50.546521

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d2d7527a07'
down_revision: Union[str, None] = 'd8c3096b71a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create component_data_providers table
    op.create_table('component_data_providers',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('api_url', sa.String(length=500), nullable=False),
        sa.Column('api_key_encrypted', sa.Text(), nullable=True),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', name='uq_provider_name')
    )

    # Create component_provider_data table
    op.create_table('component_provider_data',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('component_id', sa.String(), nullable=False),
        sa.Column('provider_id', sa.String(), nullable=False),
        sa.Column('provider_part_id', sa.String(length=255), nullable=False),
        sa.Column('datasheet_url', sa.String(length=1000), nullable=True),
        sa.Column('image_url', sa.String(length=1000), nullable=True),
        sa.Column('specifications_json', sa.JSON(), nullable=True),
        sa.Column('cached_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['component_id'], ['components.id'], ),
        sa.ForeignKeyConstraint(['provider_id'], ['component_data_providers.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('component_id', 'provider_id', name='uq_component_provider')
    )

    # Create index for cache management
    op.create_index('ix_component_provider_cached_at', 'component_provider_data', ['component_id', 'cached_at'])


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_component_provider_cached_at', table_name='component_provider_data')

    # Drop component_provider_data table
    op.drop_table('component_provider_data')

    # Drop component_data_providers table
    op.drop_table('component_data_providers')