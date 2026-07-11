from typing import Annotated, Any

from fastapi import Depends
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from ..core.config import settings

ENGINE: Engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
)


# Temporário para uso do SQLite com FK.
# Ainda mais agora que não estamos mais usando o DB do schema.
# Futuramente iremos explodir isso para colocar o Postgres
@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection: Any, _record: Any) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class DatabaseManager:
    def __init__(self, engine: Engine):
        self.engine = engine

    def session(self) -> Session:
        return Session(self.engine)


db_manager = DatabaseManager(ENGINE)


def get_db_manager() -> DatabaseManager:
    return db_manager


DatabaseManagerDep = Annotated[DatabaseManager, Depends(get_db_manager)]
