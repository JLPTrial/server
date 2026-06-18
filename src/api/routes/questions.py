from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import and_, or_
from sqlmodel import select

from ...api.dependencies.current_user import get_current_user
from ...core.config import settings
from ...database.session import DatabaseManagerDep
from ...models import Questions, User
from ...models.question import Tags, UserQuestion
from ...models.question_response import QuestionListResponse
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
    for question_database_title in settings.AVAILABLE_QUESTION_DATABASES.values():
        with db.session(question_database_title) as session:
            # Selecting all questions
            stmt = select(Questions)

            # Filter by question_id if provided
            if question_id:
                stmt = stmt.where(Questions.id == question_id)

            # Filter tag if provided
            if tag:
                stmt = stmt.join(Questions.tags).where(Tags.name.ilike(f"%{tag}%"))

            # Filter by answered status if provided
            if answered is not None:
                firebase_uid = _current_user.firebase_uid

                stmt = stmt.outerjoin(Questions.users_link)

                if answered.lower() == "true":
                    stmt = stmt.where(
                        and_(
                            UserQuestion.user_firebase_uid == firebase_uid,
                            UserQuestion.status == "answered",
                        )
                    )

                elif answered.lower() == "false":
                    stmt = stmt.where(
                        or_(
                            UserQuestion.user_firebase_uid.is_(None),
                            and_(
                                UserQuestion.user_firebase_uid == firebase_uid,
                                UserQuestion.status != "answered",
                            ),
                        )
                    )

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

    results = []
    if level_id in settings.AVAILABLE_QUESTION_DATABASES.values():
        with db.session(level_id) as session:
            # Selecting all questions
            stmt = select(Questions)

            # Filter tag if provided
            if tag:
                stmt = stmt.join(Questions.tags).where(Tags.name.ilike(f"%{tag}%"))

            # Filter by answered status if provided
            if answered is not None:
                firebase_uid = _current_user.firebase_uid

                stmt = stmt.outerjoin(Questions.users_link)

                if answered.lower() == "true":
                    stmt = stmt.where(
                        and_(
                            UserQuestion.user_firebase_uid == firebase_uid,
                            UserQuestion.status == "answered",
                        )
                    )

                elif answered.lower() == "false":
                    stmt = stmt.where(
                        or_(
                            UserQuestion.user_firebase_uid.is_(None),
                            and_(
                                UserQuestion.user_firebase_uid == firebase_uid,
                                UserQuestion.status != "answered",
                            ),
                        )
                    )

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

    results = []
    if (
        level_id in settings.AVAILABLE_QUESTION_DATABASES.values()
        and topic_id in settings.AVAILABLE_QUESTION_TOPICS
    ):
        with db.session(level_id) as session:
            # Selecting all questions
            stmt = select(Questions).where(Questions.question_type == topic_id)

            # Filter tag if provided
            if tag:
                stmt = stmt.join(Questions.tags).where(Tags.name.ilike(f"%{tag}%"))

            # Filter by answered status if provided
            if answered is not None:
                firebase_uid = _current_user.firebase_uid

                stmt = stmt.outerjoin(Questions.users_link)

                if answered.lower() == "true":
                    stmt = stmt.where(
                        and_(
                            UserQuestion.user_firebase_uid == firebase_uid,
                            UserQuestion.status == "answered",
                        )
                    )

                elif answered.lower() == "false":
                    stmt = stmt.where(
                        or_(
                            UserQuestion.user_firebase_uid.is_(None),
                            and_(
                                UserQuestion.user_firebase_uid == firebase_uid,
                                UserQuestion.status != "answered",
                            ),
                        )
                    )

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
