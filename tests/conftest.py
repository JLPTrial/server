from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from src.database import engine, init_db
from src.main import app
from src.models import User
from sqlmodel import Session, delete


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        init_db()
        yield session

        session.exec(delete(User))
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
