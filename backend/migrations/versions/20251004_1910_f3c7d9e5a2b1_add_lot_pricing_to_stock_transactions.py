"""add_lot_pricing_to_stock_transactions

Revision ID: f3c7d9e5a2b1
Revises: a7f8b9c4d5e6
Create Date: 2025-10-04 19:10:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3c7d9e5a2b1"
down_revision: str | None = "a7f8b9c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add lot_id, price_per_unit, and total_price columns to stock_transactions table."""
    # Add lot_id column for lot/batch tracking
    op.add_column(
        "stock_transactions",
        sa.Column("lot_id", sa.String(length=100), nullable=True),
    )

    # Add price_per_unit column for unit pricing
    op.add_column(
        "stock_transactions",
        sa.Column("price_per_unit", sa.Numeric(precision=10, scale=4), nullable=True),
    )

    # Add total_price column for total transaction price
    op.add_column(
        "stock_transactions",
        sa.Column("total_price", sa.Numeric(precision=10, scale=4), nullable=True),
    )


def downgrade() -> None:
    """Remove lot_id, price_per_unit, and total_price columns from stock_transactions table."""
    # Drop columns in reverse order
    op.drop_column("stock_transactions", "total_price")
    op.drop_column("stock_transactions", "price_per_unit")
    op.drop_column("stock_transactions", "lot_id")
