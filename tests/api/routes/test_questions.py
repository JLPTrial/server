from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from src.api.utils.cookies import SESSION_COOKIE_NAME
from src.core.config import settings
from src.core.firebase.initialization import FirebaseIdentity
from src.models import Alternatives, Questions, Statement, User


def _seed_question(
	session: Session, *, question_text: str, question_type: str, level: str = "N5"
) -> Questions:
	question_command = f"Escolha a resposta correta {uuid4().hex}"
	statement = Statement(question_command=question_command)
	alternative = Alternatives(
		alternative_1="A",
		alternative_2="B",
		alternative_3="C",
		alternative_4="D",
		correct_alternative=1,
	)
	session.add(statement)
	session.add(alternative)
	session.commit()
	session.refresh(statement)
	session.refresh(alternative)

	question = Questions(
		uid=f"{level}-test-{uuid4().hex}",
		level=level,
		alternative_id=alternative.id,
		statement_id=statement.id,
		question_text=question_text,
		question_type=question_type,
	)
	session.add(question)
	session.commit()
	session.refresh(question)
	return question


def test_question_requires_login(client: TestClient, monkeypatch) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)
	response = client.get("/levels/5/questions")

	assert response.status_code == 401
	assert response.json()["detail"] == "Invalid Firebase session cookie"


def test_level_questions_return_item_when_logged_in(
	client: TestClient, db_engine, monkeypatch
) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)

	with Session(db_engine) as session:
		question = _seed_question(
			session,
			question_text="Qual alternativa está correta?",
			question_type="grammar",
		)

	monkeypatch.setattr(
		"src.api.services.login.verify_firebase_session_cookie",
		lambda session_cookie: FirebaseIdentity(
			uid="firebase-uid-abc",
			email="user@jlptrial.com",
			name="User",
		),
	)
	monkeypatch.setattr(
		"src.api.services.login._get_user_by_firebase_uid",
		lambda session, firebase_uid: User(
			firebase_uid=firebase_uid,
			email="user@jlptrial.com",
			name="User",
		),
	)

	client.cookies.set(SESSION_COOKIE_NAME, "firebase-session-cookie", path="/")
	response = client.get("/levels/5/questions")
	client.cookies.clear()

	assert response.status_code == 200
	body = response.json()
	assert body["page"] == 1
	assert body["limit"] == 20
	assert body["total"] == 1
	assert len(body["items"]) == 1
	assert body["items"][0]["id"] == question.id
	assert body["items"][0]["question_text"] == "Qual alternativa está correta?"
	assert body["items"][0]["statement"]["question_command"] is not None
	assert body["items"][0]["alternatives"]["correct_alternative"] == 1
	assert body["items"][0]["media"] is None
	assert body["items"][0]["tags"] == []


def test_questions_aggregate_multiple_levels(
	client: TestClient, db_engine, monkeypatch
) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)

	with Session(db_engine) as session:
		question_n4 = _seed_question(
			session,
			question_text="Pergunta do N4",
			question_type="vocabulary",
			level="N4",
		)
		question_n5 = _seed_question(
			session,
			question_text="Pergunta do N5",
			question_type="grammar",
			level="N5",
		)
		question_ids = {question_n4.id, question_n5.id}

	monkeypatch.setattr(
		"src.api.services.login.verify_firebase_session_cookie",
		lambda session_cookie: FirebaseIdentity(
			uid="firebase-uid-abc",
			email="user@jlptrial.com",
			name="User",
		),
	)
	monkeypatch.setattr(
		"src.api.services.login._get_user_by_firebase_uid",
		lambda session, firebase_uid: User(
			firebase_uid=firebase_uid,
			email="user@jlptrial.com",
			name="User",
		),
	)

	client.cookies.set(SESSION_COOKIE_NAME, "firebase-session-cookie", path="/")
	response = client.get("/questions")
	client.cookies.clear()

	assert response.status_code == 200
	body = response.json()
	assert body["total"] == 2
	assert {item["id"] for item in body["items"]} == question_ids
