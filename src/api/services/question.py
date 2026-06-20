from typing import Any, cast

from ...core.config import settings
from ...models.question import Questions, QuestionStatus, Tags, UserQuestion


def get_available_question_databases_ids() -> list[str]:
    return list(settings.AVAILABLE_QUESTION_DATABASES.values())


def get_question_database_title(database_id: int) -> str:
    return settings.AVAILABLE_QUESTION_DATABASES[database_id]


# Validations
def validate_question_database_id(database_id: int | None) -> bool:
    return database_id in settings.AVAILABLE_QUESTION_DATABASES


def validate_question_topic(topic: str | None) -> bool:
    return topic in settings.AVAILABLE_QUESTION_TOPICS


# Filters
def add_filter_question_id(stmt: Any, question_id: int | None) -> Any:
    if question_id:
        return stmt.where(Questions.id == question_id)
    return stmt


def add_filter_topic(stmt: Any, topic: str | None) -> Any:
    if topic:
        return stmt.where(Questions.question_type == topic)
    return stmt


def add_filter_tag(stmt: Any, tag: str | None) -> Any:
    if tag:
        # Eu realmente não gosto de usar cast, mas aparentemente, o mypy sofre sem ele...
        return stmt.join(Questions.tags).where(cast(Any, Tags.name).ilike(f"%{tag}%"))
    return stmt


def add_filter_answered(stmt: Any, answered: str | None, user_firebase_uid: str) -> Any:
    if not answered or answered == "false" or not user_firebase_uid:
        return stmt

    return stmt.outerjoin(Questions.users_link).where(
        (UserQuestion.user_firebase_uid == user_firebase_uid)
        & (
            (UserQuestion.status == QuestionStatus.CORRECT)
            | (UserQuestion.status == QuestionStatus.INCORRECT)
        )
    )
