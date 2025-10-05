"""add_fuzzy_search_indexes

Revision ID: 4d5e6f7a8b9c
Revises: 3c4d5e6f7a8b
Create Date: 2025-10-05 12:03:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4d5e6f7a8b9c"
down_revision: str | None = "3c4d5e6f7a8b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add indexes on manufacturer and package columns for improved fuzzy search performance.

    Note: SQLite doesn't support case-insensitive indexes natively like PostgreSQL.
    Case-insensitivity should be handled at the query level using COLLATE NOCASE
    or LOWER() functions. These indexes will still improve query performance for
    fuzzy matching operations.
    """
    with op.batch_alter_table("components", schema=None) as batch_op:
        # The manufacturer column already has an index from the initial schema
        # Check if we need to recreate it or add additional indexes
        # Add package index if not already present (package column exists but may not be indexed)
        batch_op.create_index(
            batch_op.f("ix_components_package"),
            ["package"],
            unique=False,
        )


def downgrade() -> None:
    """Remove fuzzy search indexes from components table."""
    with op.batch_alter_table("components", schema=None) as batch_op:
        # Drop package index
        batch_op.drop_index(batch_op.f("ix_components_package"))
