from sqlmodel import SQLModel

from .session import ENGINES


def init_db() -> None:
    for engine in ENGINES.values():
        SQLModel.metadata.create_all(engine)
