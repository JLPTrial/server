from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from src.api.utils.cookies import SESSION_COOKIE_NAME
from src.core.config import settings
from src.models import Alternatives, Questions, Statement, Tags, User, UserQuestion
from src.models.question import AnswerStatus
from tests.conftest import client, db_engine


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
		"src.api.dependencies.current_user.get_user_from_session_cookie",
		lambda db, session_cookie: User(firebase_uid=firebase_uid),
	)
	client.cookies.set(SESSION_COOKIE_NAME, "firebase-session-cookie", path="/")


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
	response = client.get(f"/statistics{query}")
	assert response.status_code == 200
	return response.json()


def test_statistics_returns_correct_summary(client: TestClient, db_engine, monkeypatch) -> None:
    monkeypatch.setattr(settings, "SECURE_REQUEST", True)
    _seed_statistics_scenario(db_engine)
    _authenticate(client, monkeypatch, "firebase-uid-abc")
	
    for period in ["all", "day", "week", "month", "year"]:

        stats = _get_statistics(client, query=f"?period={period}")

        assert stats["summary"]["answered"] == 2
        assert stats["summary"]["correct"] == 1
        assert stats["summary"]["incorrect"] == 1
        assert stats["summary"]["accuracy"] == 50.0