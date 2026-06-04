from uuid import uuid4

from fastapi.testclient import TestClient

from src.api.utils.cookies import SESSION_COOKIE_NAME
from src.core.config import settings
from src.core.firebase.initialization import FirebaseIdentity
from src.models import Alternatives, Questions, Statement, User


def test_question_requires_login(client: TestClient, monkeypatch) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)
	response = client.get("/questions/1")

	assert response.status_code == 401
	assert response.json()["detail"] == "Invalid Firebase session cookie"


def test_question_returns_item_when_logged_in(client: TestClient, db, monkeypatch) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)
	question_command = f"Escolha a resposta correta {uuid4().hex}"
	statement = Statement(question_command=question_command)
	alternative = Alternatives(
		alternative_1="A",
		alternative_2="B",
		alternative_3="C",
		alternative_4="D",
		correct_alternative=1,
	)
	db.add(statement)
	db.add(alternative)
	db.commit()
	db.refresh(statement)
	db.refresh(alternative)

	question = Questions(
		alternative_id=alternative.id,
		statement_id=statement.id,
		question_text="Qual alternativa está correta?",
		question_type="grammar",
	)
	db.add(question)
	db.commit()
	db.refresh(question)

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
	response = client.get(f"/questions/{question.id}")
	client.cookies.clear()

	assert response.status_code == 200
	body = response.json()
	assert body["id"] == question.id
	assert body["statement"]["question_command"] == question_command
	assert body["question_text"] == "Qual alternativa está correta?"
	assert body["alternatives"]["correct_alternative"] == 1
	assert body["media"] is None
	assert body["tags"] == []