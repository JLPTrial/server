from sqlmodel import SQLModel

from .. import models  # noqa: F401  # Esse import é necessário mesmo que não evidente para puxar os objetos a serem carregados.
from .session import ENGINE


def init_db() -> None:
    SQLModel.metadata.create_all(ENGINE)
