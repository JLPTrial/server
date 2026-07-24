from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from src.api.utils.cookies import SESSION_COOKIE_NAME
from src.core.config import settings
from src.core.firebase.initialization import FirebaseIdentity
from src.models import Alternatives, Questions, Statement, Tags, User, UserQuestion
from src.models.question import AnswerStatus


def _seed_question(
	session: Session,
	*,
	question_text: str,
	question_type: str,
	level: str = "N5",
	alternative_4: str | None = "D",
	correct_alternative: int = 1,
	tags: list[str] | None = None,
) -> Questions:
	question_command = f"Escolha a resposta correta {uuid4().hex}"
	statement = Statement(question_command=question_command)
	alternative = Alternatives(
		alternative_1="A",
		alternative_2="B",
		alternative_3="C",
		alternative_4=alternative_4,
		correct_alternative=correct_alternative,
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
	for tag_name in tags or []:
		tag = session.exec(select(Tags).where(Tags.name == tag_name)).first()
		if tag is None:
			tag = Tags(name=tag_name)
		question.tags.append(tag)

	session.add(question)
	session.commit()
	session.refresh(question)
	return question


def _seed_user(session: Session, firebase_uid: str) -> User:
	user = User(firebase_uid=firebase_uid)
	session.add(user)
	session.commit()
	return user


def _authenticate(client: TestClient, monkeypatch, firebase_uid: str) -> None:
	monkeypatch.setattr(
		"src.api.services.login.verify_firebase_session_cookie",
		lambda session_cookie: FirebaseIdentity(
			uid=firebase_uid,
			email="user@jlptrial.com",
			name="User",
		),
	)
	monkeypatch.setattr(
		"src.api.services.login._get_user_by_firebase_uid",
		lambda session, firebase_uid: User(firebase_uid=firebase_uid),
	)
	client.cookies.set(SESSION_COOKIE_NAME, "firebase-session-cookie", path="/")


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
		lambda session, firebase_uid: User(firebase_uid=firebase_uid),
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
	assert body["items"][0]["uid"] == question.uid
	assert body["items"][0]["level"] == "N5"
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
		lambda session, firebase_uid: User(firebase_uid=firebase_uid),
	)

	client.cookies.set(SESSION_COOKIE_NAME, "firebase-session-cookie", path="/")
	response = client.get("/questions")
	client.cookies.clear()

	assert response.status_code == 200
	body = response.json()
	assert body["total"] == 2
	assert {item["id"] for item in body["items"]} == question_ids


def _register_answer(
	client: TestClient, question_uid: str, selected_alternative: int
):
	return client.post(
		"/questions/register",
		json={
			"question_uid": question_uid,
			"selected_alternative": selected_alternative,
		},
	)


def test_register_question_requires_login(client: TestClient, monkeypatch) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)
	response = _register_answer(client, "N5-test-unknown", 1)

	assert response.status_code == 401
	assert response.json()["detail"] == "Invalid Firebase session cookie"


def test_register_question_stores_correct_answer(
	client: TestClient, db_engine, monkeypatch
) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)

	with Session(db_engine) as session:
		_seed_user(session, "firebase-uid-abc")
		question = _seed_question(
			session,
			question_text="Qual alternativa está correta?",
			question_type="grammar",
			correct_alternative=2,
		)

	_authenticate(client, monkeypatch, "firebase-uid-abc")
	response = _register_answer(client, question.uid, 2)
	client.cookies.clear()

	assert response.status_code == 200
	assert response.json() == {
		"question_uid": question.uid,
		"selected_alternative": 2,
		"status": "correct",
	}

	with Session(db_engine) as session:
		user_question = session.get(
			UserQuestion, ("firebase-uid-abc", question.id)
		)
		assert user_question is not None
		assert user_question.status == AnswerStatus.CORRECT
		assert user_question.selected_alternative == 2


def test_register_question_upserts_on_reanswer(
	client: TestClient, db_engine, monkeypatch
) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)

	with Session(db_engine) as session:
		_seed_user(session, "firebase-uid-abc")
		question = _seed_question(
			session,
			question_text="Qual alternativa está correta?",
			question_type="grammar",
			correct_alternative=1,
		)

	_authenticate(client, monkeypatch, "firebase-uid-abc")
	first_response = _register_answer(client, question.uid, 3)
	second_response = _register_answer(client, question.uid, 1)
	client.cookies.clear()

	assert first_response.status_code == 200
	assert first_response.json()["status"] == "incorrect"
	assert second_response.status_code == 200
	assert second_response.json()["status"] == "correct"

	with Session(db_engine) as session:
		user_questions = session.exec(select(UserQuestion)).all()
		assert len(user_questions) == 1
		assert user_questions[0].status == AnswerStatus.CORRECT
		assert user_questions[0].selected_alternative == 1


def test_register_question_unknown_uid_returns_404(
	client: TestClient, monkeypatch
) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)

	_authenticate(client, monkeypatch, "firebase-uid-abc")
	response = _register_answer(client, "N5-test-unknown", 1)
	client.cookies.clear()

	assert response.status_code == 404
	assert response.json()["detail"] == "Question not found"


def test_register_question_missing_fourth_alternative_returns_422(
	client: TestClient, db_engine, monkeypatch
) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)

	with Session(db_engine) as session:
		_seed_user(session, "firebase-uid-abc")
		question = _seed_question(
			session,
			question_text="Questão com três alternativas",
			question_type="grammar",
			alternative_4=None,
		)

	_authenticate(client, monkeypatch, "firebase-uid-abc")
	response = _register_answer(client, question.uid, 4)
	client.cookies.clear()

	assert response.status_code == 422
	assert response.json()["detail"] == "Invalid alternative for this question"

	with Session(db_engine) as session:
		assert session.exec(select(UserQuestion)).all() == []


def test_register_question_out_of_range_alternative_returns_422(
	client: TestClient, db_engine, monkeypatch
) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)

	with Session(db_engine) as session:
		_seed_user(session, "firebase-uid-abc")
		question = _seed_question(
			session,
			question_text="Qual alternativa está correta?",
			question_type="grammar",
		)

	_authenticate(client, monkeypatch, "firebase-uid-abc")
	response = _register_answer(client, question.uid, 5)
	client.cookies.clear()

	assert response.status_code == 422


def test_statistics_requires_login(client: TestClient, monkeypatch) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)
	response = client.get("/statistics/")

	assert response.status_code == 401
	assert response.json()["detail"] == "Invalid Firebase session cookie"


def _seed_statistics_scenario(db_engine) -> dict[str, int]:
	"""4 questões (N5 grammar+tag, N5 kanji, N4 grammar, N4 vocabulary+tag),
	com o usuário acertando a primeira e errando a segunda. Retorna os ids."""
	with Session(db_engine) as session:
		_seed_user(session, "firebase-uid-abc")
		questions = {
			"n5_grammar": _seed_question(
				session,
				question_text="N5 grammar",
				question_type="grammar",
				level="N5",
				tags=["partículas"],
			),
			"n5_kanji": _seed_question(
				session,
				question_text="N5 kanji",
				question_type="kanji",
				level="N5",
			),
			"n4_grammar": _seed_question(
				session,
				question_text="N4 grammar",
				question_type="grammar",
				level="N4",
			),
			"n4_vocabulary": _seed_question(
				session,
				question_text="N4 vocabulary",
				question_type="vocabulary",
				level="N4",
				tags=["partículas"],
			),
		}

		session.add(
			UserQuestion(
				user_firebase_uid="firebase-uid-abc",
				question_id=questions["n5_grammar"].id,
				status=AnswerStatus.CORRECT,
				selected_alternative=1,
			)
		)
		session.add(
			UserQuestion(
				user_firebase_uid="firebase-uid-abc",
				question_id=questions["n5_kanji"].id,
				status=AnswerStatus.INCORRECT,
				selected_alternative=2,
			)
		)
		session.commit()
		return {name: question.id for name, question in questions.items()}


def _get_statistics(client: TestClient, query: str = "") -> dict[str, int]:
	response = client.get(f"/questions/statistics{query}")
	assert response.status_code == 200
	return response.json()
