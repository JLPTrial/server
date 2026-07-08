from typing import Any, cast

from ...core.config import settings

from ...models.question import Questions, QuestionStatus, Tags, UserQuestion


# Output formatter
def wrap_output(
    questions: list[Questions], page: int, limit: int
) -> dict[str, object]:
    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "total": len(questions),
        "items": questions[start:end] if questions else [],
    }


# Settings getters
def get_available_question_databases_ids() -> list[str]:
    return list(settings.AVAILABLE_QUESTION_DATABASES.values())


def get_question_database_title(database_id: int) -> str:
    return settings.AVAILABLE_QUESTION_DATABASES[database_id]


# Validations
def validate_parameters(parameters: dict[str, Any]):
    for key, value in parameters.items():
        if key == "topic" and not validate_question_topic(value):
            return False
        if key == "level_id" and not validate_question_level_id(value):
            return False
        if key == "answered" and not validate_answered_parameter(value):
            return False
    return True


def validate_answered_parameter(answered: str | None) -> bool:
    return answered in settings.AVAILABLE_QUESTION_ANSWERED_FILTERS


def validate_question_level_id(level_id: int | None) -> bool:
    return level_id in settings.AVAILABLE_QUESTION_DATABASES


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
    if not answered or answered == "all" or not user_firebase_uid:
        return stmt

    if answered == "answered":
        return stmt.join(Questions.user_questions).where(
            UserQuestion.user_firebase_uid == user_firebase_uid
        )
    
    if answered == "unanswered":
        return stmt.where(
            ~Questions.user_questions.any(UserQuestion.user_firebase_uid == user_firebase_uid)
        )
    
    if answered == "correct":
        return stmt.join(Questions.user_questions).where(
            (UserQuestion.user_firebase_uid == user_firebase_uid) &
            (UserQuestion.status == QuestionStatus.correct)
        )
    
    if answered == "incorrect":
        return stmt.join(Questions.user_questions).where(
            (UserQuestion.user_firebase_uid == user_firebase_uid) &
            (UserQuestion.status == QuestionStatus.incorrect)
        )