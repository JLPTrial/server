from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select

from ...api.dependencies.current_user import get_current_user
from ...database.session import SessionDep
from ...models import Questions, User
from ...models.question_response import QuestionResponse

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get(
    "/{question_id}",
    response_model=QuestionResponse,
)
def read_question(
    question_id: int,
    session: SessionDep,
    _current_user: Annotated[User, Depends(get_current_user)],
) -> Questions:
    statement = select(Questions).where(Questions.id == question_id)
    question = session.exec(statement).first()
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question not found",
        )

    return question

