"""add_unique_constraint_to_part_numbers

Revision ID: 7018a49dd597
Revises: 22648520e3e9
Create Date: 2025-09-27 11:23:33.224873

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7018a49dd597'
down_revision: Union[str, None] = '22648520e3e9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add unique constraint to part_number field.
    First, handle any existing duplicate part numbers by appending a suffix.
    """
    # Get connection to execute raw SQL for duplicate handling
    connection = op.get_bind()

    # Check if components table exists before trying to clean duplicates
    inspector = sa.inspect(connection)
    if 'components' in inspector.get_table_names():
        # Step 1: Find and update duplicate part numbers (only if table exists)
        # Simpler approach that works with SQLite
        simple_update_sql = """
        UPDATE components
        SET part_number = part_number || '_' || substr(id, 1, 8)
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM components
            WHERE part_number IS NOT NULL
            GROUP BY part_number
        )
        AND part_number IS NOT NULL;
        """

        try:
            # Check if there are any duplicates first
            check_duplicates_sql = """
            SELECT COUNT(*) as duplicate_count
            FROM (
                SELECT part_number
                FROM components
                WHERE part_number IS NOT NULL
                GROUP BY part_number
                HAVING COUNT(*) > 1
            ) duplicates;
            """
            result = connection.execute(sa.text(check_duplicates_sql)).fetchone()
            duplicate_count = result[0] if result else 0

            if duplicate_count > 0:
                print(f"Found {duplicate_count} duplicate part numbers, updating...")
                connection.execute(sa.text(simple_update_sql))
                print("Duplicate part numbers updated with unique suffixes")
            else:
                print("No duplicate part numbers found")

        except Exception as e:
            print(f"Warning: Could not check/update duplicates: {e}")

        # Step 2: Add unique constraint to part_number
        try:
            with op.batch_alter_table('components', schema=None) as batch_op:
                # Try to drop the existing index first (may not exist)
                try:
                    batch_op.drop_index('ix_components_part_number')
                except:
                    pass  # Index might not exist

                # Create unique constraint (allowing NULL values, but ensuring non-NULL values are unique)
                batch_op.create_unique_constraint('uq_components_part_number', ['part_number'])

                # Recreate the index for performance
                batch_op.create_index('ix_components_part_number', ['part_number'])
        except Exception as e:
            print(f"Warning: Could not add unique constraint: {e}")
    else:
        print("Components table does not exist yet, skipping duplicate cleanup")


def downgrade() -> None:
    """Remove unique constraint from part_number field."""
    with op.batch_alter_table('components', schema=None) as batch_op:
        # Drop unique constraint
        batch_op.drop_constraint('uq_components_part_number', type_='unique')

        # The index should remain for performance