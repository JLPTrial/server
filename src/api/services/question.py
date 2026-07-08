from sqlmodel import select

from ...models.user import User
from ...models.question import Questions

from ..utils.question_formatter import format_question
from ..utils import question as question_utils

from ...database.session import DatabaseManagerDep


##################
# Route Functions
##################
def get_questions(
    db: DatabaseManagerDep,
    _current_user: User,
    question_id: int | None = None,
    tag: str | None = None,
    answered: str | None = None,
    page: int = 1,
    limit: int = 20,
):
    
    results = []
    for question_database_title in question_utils.get_available_question_databases_ids():
        with db.session(question_database_title) as session:

            # Selecting all questions
            stmt = select(Questions)

            # Filter by question_id if provided
            stmt = question_utils.add_filter_question_id(stmt, question_id)

            # Filter tag if provided
            stmt = question_utils.add_filter_tag(stmt, tag)

            # Filter by answered status if provided
            stmt = question_utils.add_filter_answered(stmt, answered, _current_user.firebase_uid)

            # Collecting results
            rows = session.exec(stmt).all()
            results.extend([format_question(q) for q in rows])

    # Return paginated response with question data
    return question_utils.wrap_output(results, page, limit)


def get_level_questions(
    db: DatabaseManagerDep,
    _current_user: User,
    level_id: int | None = None,  # 4 or 5, for example
    tag: str | None = None,
    answered: str | None = None,
    page: int = 1,
    limit: int = 20,
):
    # Validate level_id before querying the database
    if not(question_utils.validate_parameters({"level_id": level_id})):
        return question_utils.wrap_output([], page, limit)

    question_database_title = question_utils.get_question_database_title(level_id)

    results = []
    with db.session(question_database_title) as session:
        # Selecting all questions
        stmt = select(Questions)

        # Filter tag if provided
        stmt = question_utils.add_filter_tag(stmt, tag)

        # Filter by answered status if provided
        stmt = question_utils.add_filter_answered(stmt, answered, _current_user.firebase_uid)

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
    answered: str | None = None,
    page: int = 1,
    limit: int = 20,
):
    
    # Validate level_id and topic_id before querying the database
    if not(question_utils.validate_parameters({"level_id": level_id, "topic": topic_id})):
        return question_utils.wrap_output([], page, limit)
    
    question_database_title = question_utils.get_question_database_title(level_id)

    results = []
    with db.session(question_database_title) as session:
        # Selecting all questions
        stmt = select(Questions)

        # Filter by topic
        stmt = question_utils.add_filter_topic(stmt, topic_id)

        # Filter tag if provided
        stmt = question_utils.add_filter_tag(stmt, tag)

        # Filter by answered status if provided
        stmt = question_utils.add_filter_answered(stmt, answered, _current_user.firebase_uid)

        # Collecting results
        rows = session.exec(stmt).all()
        results = [format_question(q) for q in rows]

    # Return paginated response with question data
    return question_utils.wrap_output(results, page, limit)