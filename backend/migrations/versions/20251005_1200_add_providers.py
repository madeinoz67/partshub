"""add_providers

Revision ID: 1a2b3c4d5e6f
Revises: f3c7d9e5a2b1
Create Date: 2025-10-05 12:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1a2b3c4d5e6f"
down_revision: str | None = "f3c7d9e5a2b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add providers table for managing external parts providers."""
    # Create providers table
    op.create_table(
        "providers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("adapter_class", sa.String(length=200), nullable=False),
        sa.Column("base_url", sa.String(length=500), nullable=False),
        sa.Column("api_key_required", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="active",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_providers")),
        sa.UniqueConstraint("name", name=op.f("uq_providers_name")),
        sa.CheckConstraint(
            "status IN ('active', 'inactive')",
            name=op.f("ck_providers_status_valid"),
        ),
    )

    # Create indexes
    with op.batch_alter_table("providers", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_providers_name"), ["name"], unique=True)
        batch_op.create_index(batch_op.f("ix_providers_status"), ["status"], unique=False)

    # Seed default provider (LCSC)
    op.execute(
        """
        INSERT INTO providers (name, adapter_class, base_url, api_key_required, status)
        VALUES ('LCSC', 'LCSCAdapter', 'https://wmsc.lcsc.com/wmsc', 0, 'active')
        """
    )


def downgrade() -> None:
    """Remove providers table and indexes."""
    # Drop indexes first (handled automatically in batch mode)
    with op.batch_alter_table("providers", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_providers_status"))
        batch_op.drop_index(batch_op.f("ix_providers_name"))

    # Drop table
    op.drop_table("providers")
