"""add_version_column_to_components

Revision ID: a7f8b9c4d5e6
Revises: 46c323465c62
Create Date: 2025-10-04 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a7f8b9c4d5e6"
down_revision: str | None = "46c323465c62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add version column to components table for optimistic concurrency control."""
    # Add version column with default value of 1
    op.add_column(
        "components",
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
    )

    # Create index on version column for improved query performance
    op.create_index("idx_components_version", "components", ["version"])


def downgrade() -> None:
    """Remove version column and index from components table."""
    # Drop index first
    op.drop_index("idx_components_version", table_name="components")

    # Drop version column
    op.drop_column("components", "version")
