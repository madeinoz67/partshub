"""
Database configuration and session management for PartsHub backend.
"""

import os

from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

# Support environment variable override for database URL
# Use ../data to go up from backend/ to project root
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///../data/partshub.db")

# SQLite specific configuration for concurrent access and foreign keys
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30,
        # Additional SQLite performance optimizations
        "isolation_level": None,  # Enable autocommit mode for better performance
    },
    poolclass=StaticPool,
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=3600,  # Recycle connections every hour
    echo=False,  # Set to True for SQL debugging
)

# Enable foreign key constraints in SQLite


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Configure SQLite for optimal performance and reliability."""
    cursor = dbapi_connection.cursor()

    # Essential settings
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute(
        "PRAGMA journal_mode=WAL"
    )  # Write-Ahead Logging for better concurrency

    # Performance optimizations
    cursor.execute(
        "PRAGMA synchronous=NORMAL"
    )  # Balance between safety and performance
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache size (negative = KB)
    cursor.execute("PRAGMA temp_store=MEMORY")  # Store temporary tables in memory
    cursor.execute("PRAGMA mmap_size=268435456")  # 256MB memory-mapped I/O

    # Query optimization
    cursor.execute("PRAGMA optimize")  # Analyze and optimize query planner

    cursor.close()


# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base with custom metadata for consistent naming
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)

Base = declarative_base(metadata=metadata)


# Dependency injection for FastAPI
def get_db():
    """Database session dependency for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        # Rollback on any exception to ensure clean state
        db.rollback()
        raise
    finally:
        db.close()


def get_session():
    """Get a new database session for direct use in services."""
    return SessionLocal()


# Database health check utility
def check_database_health():
    """Check if database is accessible and properly configured."""
    from sqlalchemy import text

    try:
        with engine.connect() as connection:
            # Test basic connectivity
            connection.execute(text("SELECT 1"))

            # Check WAL mode is enabled
            result = connection.execute(text("PRAGMA journal_mode")).fetchone()
            if result and result[0].lower() != "wal":
                return False, "WAL mode not enabled"

            # Check foreign keys are enabled
            result = connection.execute(text("PRAGMA foreign_keys")).fetchone()
            if result and result[0] != 1:
                return False, "Foreign keys not enabled"

            return True, "Database healthy"
    except Exception as e:
        return False, f"Database error: {str(e)}"
