from typing import Annotated

from fastapi import APIRouter, Depends

from ...api.dependencies.current_user import get_current_user
from ...database.session import DatabaseManagerDep
from ...models import User
from ...models.question_response import (
    QuestionListResponse,
    QuestionRegisterRequest,
    QuestionRegisterResponse,
)
from ..services import question as question_services

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
    answer_status: str | None = None,
    random: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, object]:
    return question_services.get_questions(
        db=db,
        _current_user=_current_user,
        question_id=question_id,
        tag=tag,
        answer_status=answer_status,
        random=random,
        page=page,
        limit=limit,
    )


# Registers the answer given by the user to a question
@router.post(
    "/questions/register",
    response_model=QuestionRegisterResponse,
)
def register_question(
    db: DatabaseManagerDep,
    current_user: Annotated[User, Depends(get_current_user)],
    payload: QuestionRegisterRequest,
) -> dict[str, object]:
    return question_services.register_question(
        db=db,
        current_user=current_user,
        payload=payload,
    )


# Filters question by level
@router.get(
    "/levels/{level_id}/questions",
    response_model=QuestionListResponse,
)
def read_level_questions(
    db: DatabaseManagerDep,
    _current_user: Annotated[User, Depends(get_current_user)],
    level_id: int | None = None,  # 4 or 5, for example
    tag: str | None = None,
    answer_status: str | None = None,
    random: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, object]:
    return question_services.get_level_questions(
        db=db,
        _current_user=_current_user,
        level_id=level_id,
        tag=tag,
        answer_status=answer_status,
        random=random,
        page=page,
        limit=limit,
    )


# Filters question by level and topic
@router.get(
    "/levels/{level_id}/topics/{topic_id}/questions",
    response_model=QuestionListResponse,
)
def read_level_topic_questions(
    db: DatabaseManagerDep,
    _current_user: Annotated[User, Depends(get_current_user)],
    level_id: int | None = None,  # 4 or 5, for example
    topic_id: str | None = None,  # grammar, vocabulary, etc
    tag: str | None = None,
    answer_status: str | None = None,
    random: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, object]:
    return question_services.get_level_topic_questions(
        db=db,
        _current_user=_current_user,
        level_id=level_id,
        topic_id=topic_id,
        tag=tag,
        answer_status=answer_status,
        random=random,
        page=page,
        limit=limit,
    )


# Mock test route
@router.get(
    "/questions/mock/{level_id}/",
    response_model=QuestionListResponse,
)
def read_mock_test_questions(
    db: DatabaseManagerDep,
    _current_user: Annotated[User, Depends(get_current_user)],
    level_id: int | None = None,  # 4 or 5, for example
) -> list[dict[str, object]]:
    return question_services.get_mock_test(
        db=db,
        level_id=level_id,
    )
