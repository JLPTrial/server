from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session, delete

from src import database as database_package
from src.database import session as database_session
from src import main as main_module
from src.main import app
from src.models import User


@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("db") / "test.db"


@pytest.fixture(scope="session", autouse=True)
def db_engine(test_db_path: Path) -> Generator[object, None, None]:
    test_engine = create_engine(
        f"sqlite:///{test_db_path}",
        connect_args={"check_same_thread": False},
    )

    database_session.engine = test_engine
    database_package.engine = test_engine
    database_package.init_db = lambda: None
    main_module.init_db = lambda: None

    SQLModel.metadata.create_all(test_engine)

    yield test_engine


@pytest.fixture(scope="session", autouse=True)
def db(db_engine) -> Generator[Session, None, None]:
    with Session(db_engine) as session:
        yield session

        session.exec(delete(User))
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
