from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import select

from ...api.dependencies.current_user import get_current_user
from ...database.session import DatabaseManagerDep
from ...models import Questions, User
from ...models.question_response import QuestionListResponse
from ..services.question import (
    add_filter_answered,
    # Filters
    add_filter_question_id,
    add_filter_tag,
    add_filter_topic,
    get_available_question_databases_ids,
    validate_question_database_id,
    validate_question_topic,
)
from ..utils.question_formatter import format_question

router = APIRouter(tags=["questions"])


@router.get(
    "/questions",
    response_model=QuestionListResponse,
)
def read_questions(
    db: DatabaseManagerDep,
    _current_user: Annotated[User, Depends(get_current_user)],
    question_id: int | None = None,
    tag: str | None = None,
    answered: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, object]:

    # Pagination logic
    start = (page - 1) * limit
    end = start + limit

    results = []
    for question_database_title in get_available_question_databases_ids():
        with db.session(question_database_title) as session:
            # Selecting all questions
            stmt = select(Questions)

            # Filter by question_id if provided
            stmt = add_filter_question_id(stmt, question_id)

            # Filter tag if provided
            stmt = add_filter_tag(stmt, tag)

            # Filter by answered status if provided
            stmt = add_filter_answered(stmt, answered, _current_user.firebase_uid)

            # Collecting results
            rows = session.exec(stmt).all()
            results.extend([format_question(q) for q in rows])

    # Return paginated response with question data
    return {
        "page": page,
        "limit": limit,
        "total": len(results),
        "items": results[start:end],
    }


# Filters question by level
@router.get(
    "/levels/{level_id}/questions",
    response_model=QuestionListResponse,
)
def read_level_questions(
    db: DatabaseManagerDep,
    _current_user: Annotated[User, Depends(get_current_user)],
    level_id: str | None = None,  # N4 or N5, for example
    tag: str | None = None,
    answered: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, object]:

    # Pagination logic
    start = (page - 1) * limit
    end = start + limit

    # Validate level_id and topic_id before querying the database
    if not(validate_question_database_id(level_id)):
        return {
            "page": page,
            "limit": limit,
            "total": 0,
            "items": [],
        }

    # Querying database
    results = []
    with db.session(level_id) as session:

        # Selecting all questions
        stmt = select(Questions)

        # Filter tag if provided
        stmt = add_filter_tag(stmt, tag)

        # Filter by answered status if provided
        stmt = add_filter_answered(stmt, answered, _current_user.firebase_uid)

        # Collecting results
        rows = session.exec(stmt).all()
        results = [format_question(q) for q in rows]

    # Return paginated response with question data
    return {
        "page": page,
        "limit": limit,
        "total": len(results),
        "items": results[start:end],
    }


# Filters question by level and topic
@router.get(
    "/levels/{level_id}/topics/{topic_id}/questions",
    response_model=QuestionListResponse,
)
def read_level_topic_questions(
    db: DatabaseManagerDep,
    _current_user: Annotated[User, Depends(get_current_user)],
    level_id: str | None = None,  # N4 or N5, for example
    topic_id: str | None = None,  # grammar, vocabulary, etc
    tag: str | None = None,
    answered: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, object]:

    # Pagination logic
    start = (page - 1) * limit
    end = start + limit

    # Validate level_id and topic_id before querying the database
    if not(
        validate_question_database_id(level_id)
        and validate_question_topic(topic_id)
    ):
        return {
        "page": page,
        "limit": limit,
        "total": 0,
        "items": [],
    }

    # Querying database
    results = []
    with db.session(level_id) as session:

        # Selecting all questions
        stmt = select(Questions)

        # Filter by topic
        stmt = add_filter_topic(stmt, topic_id)

        # Filter tag if provided
        stmt = add_filter_tag(stmt, tag)

        # Filter by answered status if provided
        stmt = add_filter_answered(stmt, answered, _current_user.firebase_uid)

        # Collecting results
        rows = session.exec(stmt).all()
        results = [format_question(q) for q in rows]

    # Return paginated response with question data
    return {
        "page": page,
        "limit": limit,
        "total": len(results),
        "items": results[start:end],
    }
