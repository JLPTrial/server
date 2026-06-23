from collections.abc import Mapping
from typing import Annotated

from fastapi import Depends
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from ..core.config import settings

ENGINES: dict[str, Engine] = {
    name: create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False},
    )
    for name, path in settings.DATABASE_PATHS.items()
}


class DatabaseManager:
    def __init__(self, engines: Mapping[str, Engine]):
        self.engines = engines

    def session(self, db_name: str) -> Session:
        return Session(self.engines[db_name])


db_manager = DatabaseManager(ENGINES)


def get_db_manager() -> DatabaseManager:
    return db_manager


DatabaseManagerDep = Annotated[DatabaseManager, Depends(get_db_manager)]
