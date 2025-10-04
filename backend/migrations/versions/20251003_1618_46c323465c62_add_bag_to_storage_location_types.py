"""add_bag_to_storage_location_types

Revision ID: 46c323465c62
Revises: babe5de6fd9f
Create Date: 2025-10-03 16:18:03.021224

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46c323465c62'
down_revision: Union[str, None] = 'babe5de6fd9f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite requires batch mode to modify constraints
    with op.batch_alter_table('storage_locations', schema=None) as batch_op:
        batch_op.drop_constraint('ck_storage_location_type_valid', type_='check')
        batch_op.create_check_constraint(
            'ck_storage_location_type_valid',
            "type IN ('container', 'room', 'building', 'cabinet', 'drawer', 'shelf', 'bin', 'bag')"
        )


def downgrade() -> None:
    # SQLite requires batch mode to modify constraints
    with op.batch_alter_table('storage_locations', schema=None) as batch_op:
        batch_op.drop_constraint('ck_storage_location_type_valid', type_='check')
        batch_op.create_check_constraint(
            'ck_storage_location_type_valid',
            "type IN ('container', 'room', 'building', 'cabinet', 'drawer', 'shelf', 'bin')"
        )