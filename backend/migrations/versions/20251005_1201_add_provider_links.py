"""add_provider_links

Revision ID: 2b3c4d5e6f7a
Revises: 1a2b3c4d5e6f
Create Date: 2025-10-05 12:01:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2b3c4d5e6f7a"
down_revision: str | None = "1a2b3c4d5e6f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add provider_links table for linking components to external providers."""
    # Create provider_links table
    op.create_table(
        "provider_links",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("component_id", sa.String(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("provider_part_number", sa.String(length=100), nullable=False),
        sa.Column("provider_url", sa.String(length=500), nullable=False),
        sa.Column(
            "sync_status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["component_id"],
            ["components.id"],
            name=op.f("fk_provider_links_component_id_components"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["provider_id"],
            ["providers.id"],
            name=op.f("fk_provider_links_provider_id_providers"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_provider_links")),
        sa.UniqueConstraint(
            "component_id",
            "provider_id",
            name=op.f("uq_provider_links_component_id_provider_id"),
        ),
        sa.CheckConstraint(
            "sync_status IN ('synced', 'pending', 'failed')",
            name=op.f("ck_provider_links_sync_status_valid"),
        ),
    )

    # Create indexes
    with op.batch_alter_table("provider_links", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_provider_links_provider_part_number"),
            ["provider_part_number"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_provider_links_component_id"),
            ["component_id"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_provider_links_provider_id"),
            ["provider_id"],
            unique=False,
        )


def downgrade() -> None:
    """Remove provider_links table and indexes."""
    # Drop indexes first (handled automatically in batch mode)
    with op.batch_alter_table("provider_links", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_provider_links_provider_id"))
        batch_op.drop_index(batch_op.f("ix_provider_links_component_id"))
        batch_op.drop_index(batch_op.f("ix_provider_links_provider_part_number"))

    # Drop table
    op.drop_table("provider_links")
