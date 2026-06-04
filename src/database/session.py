from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, create_engine

from ..core.config import settings

engine = create_engine(
    f"sqlite:///{settings.SQLITE_FILE}",
    connect_args={"check_same_thread": False},
)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
