from typing import Any, cast

from ...core.config import settings
from ...models.question import Questions, QuestionStatus, Tags, UserQuestion


# Output formatter
def wrap_output(
    questions: list[dict[str, object]], page: int, limit: int
) -> dict[str, object]:
    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "total": len(questions),
        "items": questions[start:end] if questions else [],
    }


def wrap_statistics_output(*, total: int, correct: int, incorrect: int) -> dict[str, object]:
    return {
        "total": total,
        "answered": correct + incorrect,
        "correct": correct,
        "incorrect": incorrect,
    }


# Settings getters
def get_available_levels() -> list[str]:
    return list(settings.AVAILABLE_QUESTION_LEVELS.values())


def get_level_name(level_id: int) -> str:
    return settings.AVAILABLE_QUESTION_LEVELS[level_id]


# Validations
def validate_parameters(parameters: dict[str, Any]) -> bool:
    for key, value in parameters.items():
        if key == "topic" and not validate_question_topic(value):
            return False
        if key == "level_id" and not validate_question_level_id(value):
            return False
        if key == "answer_status" and not validate_answer_status_parameter(value):
            return False
    return True


def validate_answer_status_parameter(answer_status: str | None) -> bool:
    return answer_status in settings.AVAILABLE_QUESTION_ANSWER_STATUSES


def validate_question_level_id(level_id: int | None) -> bool:
    return level_id in settings.AVAILABLE_QUESTION_LEVELS


def validate_question_topic(topic: str | None) -> bool:
    return topic in settings.AVAILABLE_QUESTION_TOPICS


# Filters
def add_filter_level(stmt: Any, level: str | None) -> Any:
    if level:
        return stmt.where(Questions.level == level)
    return stmt


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


def add_filter_answer_status(
    stmt: Any, answer_status: str | None, user_firebase_uid: str
) -> Any:
    if not answer_status or answer_status == "all" or not user_firebase_uid:
        return stmt

    if answer_status == "answered":
        return stmt.join(Questions.users_link).where(
            UserQuestion.user_firebase_uid == user_firebase_uid
        )

    if answer_status == "unanswered":
        return stmt.where(
            ~cast(Any, Questions.users_link).any(
                UserQuestion.user_firebase_uid == user_firebase_uid
            )
        )

    if answer_status == "correct":
        return stmt.join(Questions.users_link).where(
            (UserQuestion.user_firebase_uid == user_firebase_uid)
            & (UserQuestion.status == QuestionStatus.CORRECT)
        )

    if answer_status == "incorrect":
        return stmt.join(Questions.users_link).where(
            (UserQuestion.user_firebase_uid == user_firebase_uid)
            & (UserQuestion.status == QuestionStatus.INCORRECT)
        )
