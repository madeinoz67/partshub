"""add_attachment_image_fields

Revision ID: 002dae602c58
Revises: c2d2d7527a07
Create Date: 2025-09-26 14:06:54.521361

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002dae602c58'
down_revision: Union[str, None] = 'c2d2d7527a07'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to attachments table for image handling
    op.add_column('attachments', sa.Column('is_primary_image', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('attachments', sa.Column('thumbnail_path', sa.String(length=500), nullable=True))
    op.add_column('attachments', sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('attachments', 'display_order')
    op.drop_column('attachments', 'thumbnail_path')
    op.drop_column('attachments', 'is_primary_image')