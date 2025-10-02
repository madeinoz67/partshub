import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the parent directory of backend to sys.path so we can import src as a package
backend_path = os.path.dirname(os.path.dirname(__file__))
src_parent = os.path.dirname(backend_path)
if src_parent not in sys.path:
    sys.path.insert(0, src_parent)

# Now we can import src.models which will work with relative imports
# First import the database to get Base
from backend.src.database import Base  # noqa: E402

# Import all models to register them with Base.metadata
# ruff: noqa: F401, E402
from backend.src.models import (
    APIToken,
    Attachment,
    Category,
    Component,
    ComponentDataProvider,
    ComponentLocation,
    ComponentProviderData,
    CustomField,
    CustomFieldValue,
    FieldType,
    KiCadLibraryData,
    MetaPart,
    MetaPartComponent,
    Project,
    ProjectComponent,
    ProjectStatus,
    Purchase,
    PurchaseItem,
    StockTransaction,
    StorageLocation,
    Substitute,
    Supplier,
    Tag,
    TransactionType,
    User,
    component_tags,
)

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    # Check for DATABASE_URL environment variable first
    url = os.environ.get("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # Override with DATABASE_URL environment variable if present
    configuration = config.get_section(config.config_ini_section)
    if "DATABASE_URL" in os.environ:
        configuration["sqlalchemy.url"] = os.environ["DATABASE_URL"]

    # Add SQLite-specific connection args for migrations
    # Match settings from main application to avoid conflicts
    configuration["connect_args"] = {
        "check_same_thread": False,
        "timeout": 60,  # Longer timeout for migrations
    }

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Use NullPool to avoid connection pool conflicts
    )

    with connectable.connect() as connection:
        # Enable SQLite pragmas for migration compatibility
        from sqlalchemy import text
        connection.execute(text("PRAGMA foreign_keys=ON"))
        connection.execute(text("PRAGMA journal_mode=WAL"))
        connection.execute(text("PRAGMA synchronous=NORMAL"))
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            transaction_per_migration=True,  # Commit after each migration step
            render_as_batch=True,  # Better handling for SQLite ALTER operations
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
