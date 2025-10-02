"""add_layout_config_to_storage_locations

Revision ID: de3ee8af3af4
Revises: 8d9e6ce58998
Create Date: 2025-10-02 13:21:18.575522

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'de3ee8af3af4'
down_revision: Union[str, None] = '8d9e6ce58998'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add layout_config JSON column to storage_locations table."""
    # Add nullable JSON column for storing layout configuration
    # SQLite stores JSON as TEXT internally, so sa.JSON() is appropriate
    op.add_column(
        'storage_locations',
        sa.Column('layout_config', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    """Remove layout_config column from storage_locations table."""
    op.drop_column('storage_locations', 'layout_config')