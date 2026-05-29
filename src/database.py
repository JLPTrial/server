"""Database engine and helper for creating the SQLite database tables.

This module exposes an `engine` created from the configured SQLite file
and a helper `create_db_and_tables()` that initializes metadata.
"""

from sqlmodel import SQLModel, create_engine

# Path to the SQLite file used by the application.
SQLITE_FILE = "../data/N5/N5.db"

# SQLAlchemy URL for the SQLite engine.
SQLITE_URL = f"sqlite:///{SQLITE_FILE}"

engine = create_engine(SQLITE_URL)


def create_db_and_tables():
    """Create all database tables declared in SQLModel metadata.

    Returns the SQLAlchemy engine used to create the tables.
    """

    SQLModel.metadata.create_all(engine)
    return engine
