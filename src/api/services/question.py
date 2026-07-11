from typing import cast

from sqlmodel import select

from ...database.session import DatabaseManagerDep
from ...models.question import Questions
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
