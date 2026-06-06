from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from ..core.config import settings

ENGINES = {
    name: create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
    )
    for name, path in settings.DATABASE_PATHS.items()
}

class DatabaseManager:
    def __init__(self, engines: dict[str, object]):
        self.engines = engines

    def session(self, db_name: str) -> Session:
        return Session(self.engines[db_name])

db_manager = DatabaseManager(ENGINES)

def get_db_manager() -> DatabaseManager:
    return db_manager

DatabaseManagerDep = Annotated[
    DatabaseManager,
    Depends(get_db_manager)
]

    
"""def get_db() -> Generator[Session, None, None]:
    with Session(ENGINES["N5"]) as session:
            yield session


SessionDep = Annotated[Session, Depends(get_db)]"""
