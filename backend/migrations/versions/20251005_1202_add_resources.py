"""add_resources

Revision ID: 3c4d5e6f7a8b
Revises: 2b3c4d5e6f7a
Create Date: 2025-10-05 12:02:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3c4d5e6f7a8b"
down_revision: str | None = "2b3c4d5e6f7a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add resources table for managing provider-linked resource files."""
    # Create resources table
    op.create_table(
        "resources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("provider_link_id", sa.Integer(), nullable=False),
        sa.Column(
            "resource_type",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column(
            "download_status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("downloaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["provider_link_id"],
            ["provider_links.id"],
            name=op.f("fk_resources_provider_link_id_provider_links"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resources")),
        sa.CheckConstraint(
            "resource_type IN ('datasheet', 'image', 'footprint', 'symbol', 'model_3d')",
            name=op.f("ck_resources_resource_type_valid"),
        ),
        sa.CheckConstraint(
            "download_status IN ('pending', 'downloading', 'complete', 'failed')",
            name=op.f("ck_resources_download_status_valid"),
        ),
    )

    # Create indexes
    with op.batch_alter_table("resources", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_resources_provider_link_id_resource_type"),
            ["provider_link_id", "resource_type"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_resources_download_status"),
            ["download_status"],
            unique=False,
        )
        batch_op.create_index(
            batch_op.f("ix_resources_provider_link_id"),
            ["provider_link_id"],
            unique=False,
        )


def downgrade() -> None:
    """Remove resources table and indexes."""
    # Drop indexes first (handled automatically in batch mode)
    with op.batch_alter_table("resources", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_resources_provider_link_id"))
        batch_op.drop_index(batch_op.f("ix_resources_download_status"))
        batch_op.drop_index(batch_op.f("ix_resources_provider_link_id_resource_type"))

    # Drop table
    op.drop_table("resources")
