from typing import cast

from fastapi import HTTPException, status
from sqlmodel import col, func, select

from ...database.session import DatabaseManagerDep
from ...models.question import Questions, QuestionStatus, UserQuestion
from ...models.question_response import QuestionRegisterRequest
from ...models.user import User
from ..utils import question as question_utils
from ..utils.question_formatter import format_question


##################
# Route Functions
##################
def get_questions(
    db: DatabaseManagerDep,
    _current_user: User,
    question_id: int | None = None,
    tag: str | None = None,
    answer_status: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, object]:
    with db.session() as session:
        # Selecting all questions
        stmt = select(Questions)

        # Filter by question_id if provided
        stmt = question_utils.add_filter_question_id(stmt, question_id)

        # Filter tag if provided
        stmt = question_utils.add_filter_tag(stmt, tag)

        # Filter by answer status if provided
        stmt = question_utils.add_filter_answer_status(
            stmt, answer_status, _current_user.firebase_uid
        )

        # Collecting results
        rows = session.exec(stmt).all()
        results = [format_question(q) for q in rows]

    # Return paginated response with question data
    return question_utils.wrap_output(results, page, limit)


def register_question(
    db: DatabaseManagerDep,
    current_user: User,
    payload: QuestionRegisterRequest,
) -> dict[str, object]:
    with db.session() as session:
        question = session.exec(
            select(Questions).where(Questions.uid == payload.question_uid)
        ).first()
        if question is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Question not found",
            )

        if question.alternatives is None:
            raise ValueError("Question has no alternatives")

        if (
            payload.selected_alternative == 4
            and question.alternatives.alternative_4 is None
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalid alternative for this question",
            )

        answer_status = (
            QuestionStatus.CORRECT
            if payload.selected_alternative == question.alternatives.correct_alternative
            else QuestionStatus.INCORRECT
        )

        user_question = session.get(
            UserQuestion, (current_user.firebase_uid, question.id)
        )
        if user_question is None:
            user_question = UserQuestion(
                user_firebase_uid=current_user.firebase_uid,
                question_id=question.id,
            )

        user_question.status = answer_status
        user_question.selected_alternative = payload.selected_alternative

        session.add(user_question)
        session.commit()

    return {
        "question_uid": payload.question_uid,
        "selected_alternative": payload.selected_alternative,
        "status": answer_status.name.lower(),
    }


def get_question_statistics(
    db: DatabaseManagerDep,
    current_user: User,
    level_id: int | None = None,
    topic: str | None = None,
    tag: str | None = None,
) -> dict[str, object]:
    parameters: dict[str, int | str] = {}
    if level_id is not None:
        parameters["level_id"] = level_id
    if topic is not None:
        parameters["topic"] = topic

    if not question_utils.validate_parameters(parameters):
        return question_utils.wrap_statistics_output(total=0, correct=0, incorrect=0)

    level = question_utils.get_level_name(level_id) if level_id is not None else None

    with db.session() as session:
        stmt = select(Questions.id)
        stmt = question_utils.add_filter_level(stmt, level)
        stmt = question_utils.add_filter_topic(stmt, topic)
        stmt = question_utils.add_filter_tag(stmt, tag)

        question_ids = stmt.distinct()

        total = session.exec(
            select(func.count()).select_from(question_ids.subquery())
        ).one()

        status_column = col(UserQuestion.status)
        status_counts = session.exec(
            select(status_column, func.count())
            .where(UserQuestion.user_firebase_uid == current_user.firebase_uid)
            .where(col(UserQuestion.question_id).in_(question_ids))
            .group_by(status_column)
        ).all()
        counts = dict(status_counts)

    return question_utils.wrap_statistics_output(
        total=total,
        correct=counts.get(QuestionStatus.CORRECT, 0),
        incorrect=counts.get(QuestionStatus.INCORRECT, 0),
    )


def get_level_questions(
    db: DatabaseManagerDep,
    _current_user: User,
    level_id: int | None = None,  # 4 or 5, for example
    tag: str | None = None,
    answer_status: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, object]:
    # Validate level_id before querying the database
    if not (question_utils.validate_parameters({"level_id": level_id})):
        return question_utils.wrap_output([], page, limit)

    level = question_utils.get_level_name(cast(int, level_id))

    with db.session() as session:
        # Selecting all questions
        stmt = select(Questions)

        # Filter by level
        stmt = question_utils.add_filter_level(stmt, level)

        # Filter tag if provided
        stmt = question_utils.add_filter_tag(stmt, tag)

        # Filter by answer status if provided
        stmt = question_utils.add_filter_answer_status(
            stmt, answer_status, _current_user.firebase_uid
        )

        # Collecting results
        rows = session.exec(stmt).all()
        results = [format_question(q) for q in rows]

    # Return paginated response with question data
    return question_utils.wrap_output(results, page, limit)


def get_level_topic_questions(
    db: DatabaseManagerDep,
    _current_user: User,
    level_id: int | None = None,  # 4 or 5, for example
    topic_id: str | None = None,  # grammar, vocabulary, etc
    tag: str | None = None,
    answer_status: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict[str, object]:
    # Validate level_id and topic_id before querying the database
    if not (
        question_utils.validate_parameters({"level_id": level_id, "topic": topic_id})
    ):
        return question_utils.wrap_output([], page, limit)

    level = question_utils.get_level_name(cast(int, level_id))

    with db.session() as session:
        # Selecting all questions
        stmt = select(Questions)

        # Filter by level
        stmt = question_utils.add_filter_level(stmt, level)

        # Filter by topic
        stmt = question_utils.add_filter_topic(stmt, topic_id)

        # Filter tag if provided
        stmt = question_utils.add_filter_tag(stmt, tag)

        # Filter by answer status if provided
        stmt = question_utils.add_filter_answer_status(
            stmt, answer_status, _current_user.firebase_uid
        )

        # Collecting results
        rows = session.exec(stmt).all()
        results = [format_question(q) for q in rows]

    # Return paginated response with question data
    return question_utils.wrap_output(results, page, limit)
