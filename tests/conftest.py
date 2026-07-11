from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel

from src import database as database_package
from src import main as main_module
from src.database import session as database_session
from src.main import app


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("db") / "test.db"


@pytest.fixture()
def db_engine(tmp_path_factory: pytest.TempPathFactory) -> Generator[Engine, None, None]:
    test_db_dir = tmp_path_factory.mktemp("dbs")
    test_engine = create_engine(
        f"sqlite:///{test_db_dir / 'server.db'}",
        connect_args={"check_same_thread": False},
    )

    database_session.ENGINE = test_engine
    database_session.db_manager.engine = test_engine
    database_package.init_db = lambda: None
    main_module.init_db = lambda: None

    SQLModel.metadata.create_all(test_engine)

    yield test_engine


@pytest.fixture()
def db(db_engine) -> Generator[Session, None, None]:
    with Session(db_engine) as session:
        yield session


@pytest.fixture()
def client(db_engine) -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
