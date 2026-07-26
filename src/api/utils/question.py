from datetime import datetime, timedelta
from random import shuffle
from typing import Any

from sqlmodel import col

from ...core.config import settings
from ...models.question import AnswerStatus, Questions, Tags, UserQuestion


# Output formatter
def wrap_output(
    questions: list[dict[str, object]], page: int, limit: int, random: str | None = None
) -> dict[str, object]:
    start = (page - 1) * limit
    end = start + limit

    # Apply randomization if requested
    if random and random.lower() == "true":
        shuffle(questions)

    return {
        "page": page,
        "limit": limit,
        "total": len(questions),
        "items": questions[start:end] if questions else [],
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
    return topic in settings.AVAILABLE_QUESTION_TYPES

def validate_period(period: str | None) -> bool:
    return period in settings.AVAILABLE_STATISTICS_PERIODS

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
        return stmt.join(Questions.tags).where(col(Tags.name).ilike(f"%{tag}%"))
    return stmt


def add_filter_statement_id(stmt: Any, statement_id: int | None) -> Any:
    if statement_id:
        return stmt.where(Questions.statement_id == statement_id)
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
            ~col(Questions.users_link).any(
                col(UserQuestion.user_firebase_uid) == user_firebase_uid
            )
        )

    if answer_status == "correct":
        return stmt.join(Questions.users_link).where(
            (UserQuestion.user_firebase_uid == user_firebase_uid)
            & (UserQuestion.status == AnswerStatus.CORRECT)
        )

    if answer_status == "incorrect":
        return stmt.join(Questions.users_link).where(
            (UserQuestion.user_firebase_uid == user_firebase_uid)
            & (UserQuestion.status == AnswerStatus.INCORRECT)
        )




def period_to_start_date(period: str) -> datetime | None:
    now = datetime.now()

    if period == "all":
        return None
    elif period == "day":
        return now - timedelta(days=1)
    elif period == "week":
        return now - timedelta(weeks=1)
    elif period == "month":
        return now - timedelta(days=30)
    elif period == "year":
        return now - timedelta(days=365)

    raise ValueError(f"Invalid period: {period}")

def get_timeline_bucket(date: datetime, period: str) -> str:
    if period == "day":
        return date.strftime("%Y-%m-%d")

    if period == "week":
        return date.strftime("%Y-%m-%d")

    if period == "month":
        return date.strftime("%Y-%m")

    if period == "year":
        return date.strftime("%Y")

    if period == "all":
        return date.strftime("%Y")

    raise ValueError(f"Invalid period: {period}")
