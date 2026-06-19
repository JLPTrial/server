from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel

from src import database as database_package
from src import main as main_module
from src.core.config import settings
from src.database import session as database_session
from src.main import app


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("db") / "test.db"


@pytest.fixture()
def db_engines(tmp_path_factory: pytest.TempPathFactory) -> Generator[dict[str, Engine], None, None]:
    test_db_dir = tmp_path_factory.mktemp("dbs")
    test_engines = {
        db_name: create_engine(
            f"sqlite:///{test_db_dir / f'{db_name}.db'}",
            connect_args={"check_same_thread": False},
        )
        for db_name in settings.DATABASE_PATHS
    }

    database_session.ENGINES.clear()
    database_session.ENGINES.update(test_engines)
    database_package.init_db = lambda: None
    main_module.init_db = lambda: None

    for test_engine in test_engines.values():
        SQLModel.metadata.create_all(test_engine)

    yield test_engines


@pytest.fixture()
def db(db_engines) -> Generator[Session, None, None]:
    with Session(db_engines["users"]) as session:
        yield session


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
