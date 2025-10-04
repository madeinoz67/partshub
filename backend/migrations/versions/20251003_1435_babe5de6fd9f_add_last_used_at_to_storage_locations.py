"""add_last_used_at_to_storage_locations

Revision ID: babe5de6fd9f
Revises: de3ee8af3af4
Create Date: 2025-10-03 14:35:39.822091

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'babe5de6fd9f'
down_revision: Union[str, None] = 'de3ee8af3af4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add last_used_at column to storage_locations table
    op.add_column('storage_locations', sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove last_used_at column from storage_locations table
    op.drop_column('storage_locations', 'last_used_at')