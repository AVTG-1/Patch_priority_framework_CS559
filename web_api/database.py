"""
Database configuration and session management

Sets up SQLAlchemy with SQLite for development.
Provides database session and initialization utilities.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
import os
from pathlib import Path

from config import settings

# Determine database URL
# For SQLite, ensure the directory exists
if settings.database_url.startswith("sqlite"):
    # Extract file path from SQLite URL
    db_path = settings.database_url.replace("sqlite:///", "")
    if db_path and not db_path.startswith(":memory:"):
        # Create directory if it doesn't exist
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=settings.debug  # Log SQL queries in debug mode
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Yields:
        Session: SQLAlchemy database session

    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database.

    Creates all tables defined in models if they don't exist.
    Should be called on application startup.

    Example:
        from database import init_db
        init_db()
    """
    # Import all models to ensure they are registered with Base
    from models import User, SystemConfig, SimulationRun, CommunityVulnerability

    # Create all tables
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {settings.database_url}")


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data!
    Only use in development/testing.
    """
    Base.metadata.drop_all(bind=engine)
    print("All database tables dropped")


def reset_db() -> None:
    """
    Reset database by dropping and recreating all tables.

    WARNING: This will delete all data!
    Only use in development/testing.
    """
    drop_db()
    init_db()
    print("Database reset complete")


# Database utility functions
def get_db_session() -> Session:
    """
    Get a database session directly (not as dependency).

    Use this when you need a session outside of FastAPI endpoints.

    Returns:
        Session: SQLAlchemy database session

    Note:
        Remember to close the session when done:
        db = get_db_session()
        try:
            # Use db
        finally:
            db.close()
    """
    return SessionLocal()
