"""
Database connection configuration and session management
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Database URL - SQLite with WAL mode for better concurrent access
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/partshub.db")

# Enable WAL mode and foreign keys for SQLite
engine_args = {}
if DATABASE_URL.startswith("sqlite"):
    engine_args.update(
        {
            "poolclass": StaticPool,
            "connect_args": {
                "check_same_thread": False,
            },
            "echo": False,  # Set to True for SQL debugging
        }
    )

engine = create_engine(DATABASE_URL, **engine_args)

# Configure session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all tables in the database
    """
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)

    # Create all tables
    Base.metadata.create_all(bind=engine)


def init_sqlite_features():
    """
    Initialize SQLite-specific features like FTS5 and foreign keys
    """
    from sqlalchemy import text

    with engine.connect() as conn:
        # Enable foreign key constraints
        conn.execute(text("PRAGMA foreign_keys=ON;"))

        # Enable WAL mode for better concurrency
        conn.execute(text("PRAGMA journal_mode=WAL;"))

        # Optimize SQLite settings
        conn.execute(text("PRAGMA synchronous=NORMAL;"))
        conn.execute(text("PRAGMA cache_size=10000;"))
        conn.execute(text("PRAGMA temp_store=memory;"))

        conn.commit()
