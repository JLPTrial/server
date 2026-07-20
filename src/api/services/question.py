from typing import cast

from fastapi import HTTPException, status
from sqlmodel import col, func, select

from ...database.session import DatabaseManagerDep
from ...models.question import Questions, QuestionStatus, UserQuestion, Tags, QuestionTags
from ...models.question_response import QuestionRegisterRequest
from ...models.user import User
from ..utils import question as question_utils
from ..utils.question_formatter import format_question

from datetime import UTC, datetime, timedelta


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
        return question_utils.wrap_statistics_output_old(total=0, correct=0, incorrect=0)

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

        latest_interactions = (
            select(
                UserQuestion.question_id,
                func.max(UserQuestion.date).label("latest_date"),
            )
            .where(UserQuestion.user_firebase_uid == current_user.firebase_uid)
            .group_by(UserQuestion.question_id)
        ).subquery()

        status_counts = session.exec(
            select(UserQuestion.status, func.count())
            .join(
                latest_interactions,
                (UserQuestion.question_id == latest_interactions.c.question_id)
                & (UserQuestion.date == latest_interactions.c.latest_date),
            )
            .where(col(UserQuestion.question_id).in_(question_ids))
            .group_by(UserQuestion.status)
        ).all()

        counts = dict(status_counts)

    return question_utils.wrap_statistics_output_old(
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



######################################
# STATISTICS
######################################

def get_user_streak(
    db: DatabaseManagerDep,
    current_user: User,
) -> int:
    with db.session() as session:
        interaction_days = session.exec(
            select(func.date(UserQuestion.date))
            .where(UserQuestion.user_firebase_uid == current_user.firebase_uid)
            .distinct()
            .order_by(func.date(UserQuestion.date).desc())
        ).all()

    if not interaction_days:
        return 0

    interaction_days = set(interaction_days)

    current_day = datetime.now(UTC).date()

    # If the user hasn't interacted today, start counting from yesterday.
    if current_day not in interaction_days:
        current_day -= timedelta(days=1)

    streak = 0

    while current_day in interaction_days:
        streak += 1
        current_day -= timedelta(days=1)

    return streak


def get_period_statistics(
    db: DatabaseManagerDep,
    current_user: User,
    period: str,
) -> tuple[int, int]:
    start_date = question_utils.period_to_start_date(period)

    with db.session() as session:
        latest_interactions = (
            select(
                UserQuestion.question_id,
                func.max(UserQuestion.date).label("latest_date"),
            )
            .where(
                UserQuestion.user_firebase_uid == current_user.firebase_uid
            )
            .group_by(UserQuestion.question_id)
        )

        if start_date is not None:
            latest_interactions = latest_interactions.where(
                UserQuestion.date >= start_date
            )

        latest_interactions = latest_interactions.subquery()

        status_counts = session.exec(
            select(UserQuestion.status, func.count())
            .join(
                latest_interactions,
                (UserQuestion.question_id == latest_interactions.c.question_id)
                & (UserQuestion.date == latest_interactions.c.latest_date),
            )
            .where(
                UserQuestion.user_firebase_uid == current_user.firebase_uid
            )
            .group_by(UserQuestion.status)
        ).all()

    counts = dict(status_counts)

    return (
        counts.get(QuestionStatus.CORRECT, 0),
        counts.get(QuestionStatus.INCORRECT, 0),
    )

def get_question_type_statistics(
    db: DatabaseManagerDep,
    current_user: User,
    period: str,
) -> list[dict[str, object]]:
    
    # Convert the period ("day", "week", "month", "year", "all")
    # into a date boundary. None means no date filter.
    start_date = question_utils.period_to_start_date(period)

    with db.session() as session:
        # Find the latest interaction date for each question.
        # This removes duplicate interactions so that each question
        # contributes only its most recent status.
        latest_interactions = (
            select(
                UserQuestion.question_id,
                func.max(UserQuestion.date).label("latest_date"),
            )
            .where(
                UserQuestion.user_firebase_uid == current_user.firebase_uid
            )
            .group_by(UserQuestion.question_id)
        )

        # If a period was provided, only consider interactions inside it.
        if start_date is not None:
            latest_interactions = latest_interactions.where(
                UserQuestion.date >= start_date
            )

        latest_interactions = latest_interactions.subquery()

        # Count correct and incorrect latest interactions,
        # grouped by question type.
        results = session.exec(
            select(
                Questions.question_type,
                UserQuestion.status,
                func.count(),
            )
            .join(
                UserQuestion,
                Questions.id == UserQuestion.question_id,
            )
            .join(
                latest_interactions,
                (UserQuestion.question_id == latest_interactions.c.question_id)
                & (UserQuestion.date == latest_interactions.c.latest_date),
            )
            .where(
                UserQuestion.user_firebase_uid == current_user.firebase_uid
            )
            .group_by(
                Questions.question_type,
                UserQuestion.status,
            )
        ).all()

    # Transform the database aggregation into a dictionary structure
    # where each question type has separate correct/incorrect counters.
    statistics: dict[str, dict[str, int]] = {}

    for question_type, status, count in results:
        if question_type not in statistics:
            statistics[question_type] = {
                "correct": 0,
                "incorrect": 0,
            }

        if status == QuestionStatus.CORRECT:
            statistics[question_type]["correct"] = count
        elif status == QuestionStatus.INCORRECT:
            statistics[question_type]["incorrect"] = count

    # Convert the internal dictionary into the API response format.
    return [
        {
            "skill": question_type,
            "correct": values["correct"],
            "incorrect": values["incorrect"],
        }
        for question_type, values in statistics.items()
    ]


def get_skill_tag_statistics(
    db: DatabaseManagerDep,
    current_user: User,
    period: str,
) -> dict[str, list[dict[str, object]]]:
    start_date = question_utils.period_to_start_date(period)

    with db.session() as session:
        # Get the latest interaction for each question.
        # This removes previous attempts and keeps only the current status
        # of each question for this user.
        latest_interactions = (
            select(
                UserQuestion.question_id,
                func.max(UserQuestion.date).label("latest_date"),
            )
            .where(
                UserQuestion.user_firebase_uid == current_user.firebase_uid
            )
            .group_by(UserQuestion.question_id)
        )

        if start_date is not None:
            latest_interactions = latest_interactions.where(
                UserQuestion.date >= start_date
            )

        latest_interactions = latest_interactions.subquery()

        # Count correct/incorrect answers grouped by:
        # question_type -> tag -> status
        results = session.exec(
            select(
                Questions.question_type,
                Tags.name,
                UserQuestion.status,
                func.count(),
            )
            .join(
                UserQuestion,
                Questions.id == UserQuestion.question_id,
            )
            .join(
                QuestionTags,
                QuestionTags.question_id == Questions.id,
            )
            .join(
                Tags,
                Tags.id == QuestionTags.tag_id,
            )
            .join(
                latest_interactions,
                (UserQuestion.question_id == latest_interactions.c.question_id)
                & (UserQuestion.date == latest_interactions.c.latest_date),
            )
            .where(
                UserQuestion.user_firebase_uid == current_user.firebase_uid
            )
            .group_by(
                Questions.question_type,
                Tags.name,
                UserQuestion.status,
            )
        ).all()

    # Build:
    # {
    #     "Grammar": [
    #         {
    #             "tag": "Particles",
    #             "correct": 30,
    #             "wrong": 5
    #         }
    #     ]
    # }
    skill_tags: dict[str, dict[str, dict[str, int]]] = {}

    for question_type, tag, status, count in results:
        if question_type not in skill_tags:
            skill_tags[question_type] = {}

        if tag not in skill_tags[question_type]:
            skill_tags[question_type][tag] = {
                "correct": 0,
                "wrong": 0,
            }

        if status == QuestionStatus.CORRECT:
            skill_tags[question_type][tag]["correct"] = count
        elif status == QuestionStatus.INCORRECT:
            skill_tags[question_type][tag]["wrong"] = count

    return {
        question_type: [
            {
                "tag": tag,
                "correct": values["correct"],
                "wrong": values["wrong"],
            }
            for tag, values in tags.items()
        ]
        for question_type, tags in skill_tags.items()
    }

def get_user_timeline(
    db: DatabaseManagerDep,
    current_user: User,
    period: str,
) -> list[dict[str, object]]:
    start_date = question_utils.period_to_start_date(period)

    with db.session() as session:
        # Get the latest interaction for each question.
        latest_interactions = (
            select(
                UserQuestion.question_id,
                func.max(UserQuestion.date).label("latest_date"),
            )
            .where(
                UserQuestion.user_firebase_uid == current_user.firebase_uid
            )
            .group_by(UserQuestion.question_id)
        )

        # Apply period filtering before removing duplicates.
        if start_date is not None:
            latest_interactions = latest_interactions.where(
                UserQuestion.date >= start_date
            )

        latest_interactions = latest_interactions.subquery()

        interactions = session.exec(
            select(UserQuestion)
            .join(
                latest_interactions,
                (UserQuestion.question_id == latest_interactions.c.question_id)
                & (UserQuestion.date == latest_interactions.c.latest_date),
            )
            .where(
                UserQuestion.user_firebase_uid == current_user.firebase_uid
            )
        ).all()

    # Aggregate interactions into timeline buckets.
    timeline: dict[str, dict[str, int]] = {}

    for interaction in interactions:
        bucket = question_utils.get_timeline_bucket(
            interaction.date,
            period,
        )

        if bucket not in timeline:
            timeline[bucket] = {
                "correct": 0,
                "incorrect": 0,
            }

        if interaction.status == QuestionStatus.CORRECT:
            timeline[bucket]["correct"] += 1

        elif interaction.status == QuestionStatus.INCORRECT:
            timeline[bucket]["incorrect"] += 1

    # Sort chronologically and convert to API format.
    return [
        {
            "period": bucket,
            "correct": values["correct"],
            "incorrect": values["incorrect"],
        }
        for bucket, values in sorted(timeline.items())
    ]

def get_database_statistics(
    db: DatabaseManagerDep,
) -> dict[str, dict[str, int]]:
    with db.session() as session:
        # Count questions by JLPT level.
        level_counts = dict(
            session.exec(
                select(
                    Questions.level,
                    func.count(),
                ).group_by(Questions.level)
            ).all()
        )

        # Count questions by question type.
        question_type_counts = dict(
            session.exec(
                select(
                    Questions.question_type,
                    func.count(),
                ).group_by(Questions.question_type)
            ).all()
        )

        # Count questions by tag.
        tag_counts = dict(
            session.exec(
                select(
                    Tags.name,
                    func.count(),
                )
                .join(
                    QuestionTags,
                    QuestionTags.tag_id == Tags.id,
                )
                .group_by(Tags.name)
            ).all()
        )

    return {
        "levels": level_counts,
        "question_types": question_type_counts,
        "tags": tag_counts,
    }


def statistics(
    db: DatabaseManagerDep,
    current_user: User,
    period: str = "all",
) -> dict[str, object]:
    if not(question_utils.validate_period(period)):
        return {"invalid_period": period}
    
    # summary
    streak = get_user_streak(db, current_user)
    correct, incorrect = get_period_statistics(db, current_user, period)
    answered = correct + incorrect
    accuracy = (correct / answered) * 100 if answered > 0 else 0

    # skills (question_types)
    skills : dict[str, dict[str, str | int]] = dict()

    # skillTags
    skillTags = get_skill_tag_statistics(db, current_user, period)

    # timeline
    timeline = get_user_timeline(db, current_user, period)

    # database info
    db_info = get_database_statistics(db)

    # Return the statistics in a structured format
    return question_utils.wrap_statistics_output(
        streak=streak,
        answered=answered,
        correct=correct,
        incorrect=incorrect,
        accuracy=accuracy,
        skills=skills,
        skillTags=skillTags,
        timeline=timeline,
        totalQuestions=db_info
    )


    
