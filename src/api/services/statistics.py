from datetime import UTC, datetime, timedelta

from sqlmodel import func, select

from ...database.session import DatabaseManagerDep
from ...models.question import (
    AnswerStatus,
    Questions,
    QuestionTags,
    Tags,
    UserQuestion,
)
from ...models.user import User
from ..utils import question as question_utils
from ..utils import statistics as statistics_utils


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
    level: str = "all"  # "all", "N4", "N5"
) -> tuple[int, int]:
    level = statistics_utils.validate_question_level(level)
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

        if level is not None:
            latest_interactions = latest_interactions.join(
                Questions,
                Questions.id == UserQuestion.question_id,
            ).where(Questions.level == level)

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
        counts.get(AnswerStatus.CORRECT, 0),
        counts.get(AnswerStatus.INCORRECT, 0),
    )

def get_question_type_statistics(
    db: DatabaseManagerDep,
    current_user: User,
    period: str,
    level: str = "all"  # "all", "N4", "N5"
) -> list[dict[str, object]]:

    # Convert the period ("day", "week", "month", "year", "all")
    # into a date boundary. None means no date filter.
    start_date = question_utils.period_to_start_date(period)
    level = statistics_utils.validate_question_level(level)

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

        if level is not None:
            latest_interactions = latest_interactions.join(
                Questions,
                Questions.id == UserQuestion.question_id,
            ).where(Questions.level == level)

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

    for question_type, userQuestionStatus, count in results:
        if question_type not in statistics:
            statistics[question_type] = {
                "correct": 0,
                "incorrect": 0,
            }

        if userQuestionStatus == AnswerStatus.CORRECT:
            statistics[question_type]["correct"] = count
        elif userQuestionStatus == AnswerStatus.INCORRECT:
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
    level: str = "all",
) -> dict[str, list[dict[str, object]]]:
    start_date = question_utils.period_to_start_date(period)
    level = statistics_utils.validate_question_level(level)

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

        if level is not None:
            latest_interactions = latest_interactions.join(
                Questions,
                Questions.id == UserQuestion.question_id,
            ).where(Questions.level == level)

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

    for question_type, tag, userQuestionStatus, count in results:
        if question_type not in skill_tags:
            skill_tags[question_type] = {}

        if tag not in skill_tags[question_type]:
            skill_tags[question_type][tag] = {
                "correct": 0,
                "incorrect": 0,
            }

        if userQuestionStatus == AnswerStatus.CORRECT:
            skill_tags[question_type][tag]["correct"] = count
        elif userQuestionStatus == AnswerStatus.INCORRECT:
            skill_tags[question_type][tag]["incorrect"] = count

    return {
        question_type: [
            {
                "tag": tag,
                "correct": values["correct"],
                "incorrect": values["incorrect"],
            }
            for tag, values in tags.items()
        ]
        for question_type, tags in skill_tags.items()
    }

def get_user_timeline(
    db: DatabaseManagerDep,
    current_user: User,
    period: str,
    level: str = "all"  # "all", "N4", "N5"
) -> list[dict[str, object]]:

    start_date = question_utils.period_to_start_date(period)
    level = statistics_utils.validate_question_level(level)

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

        if level is not None:
            latest_interactions = latest_interactions.join(
                Questions,
                Questions.id == UserQuestion.question_id,
            ).where(Questions.level == level)

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

        if interaction.status == AnswerStatus.CORRECT:
            timeline[bucket]["correct"] += 1

        elif interaction.status == AnswerStatus.INCORRECT:
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
    level: str = "all",
) -> dict[str, dict[str, int]]:
    level = statistics_utils.validate_question_level(level)

    with db.session() as session:
        level_query = (
            select(
                Questions.level,
                func.count(),
            )
            .group_by(Questions.level)
        )

        question_type_query = (
            select(
                Questions.question_type,
                func.count(),
            )
            .group_by(Questions.question_type)
        )

        tag_query = (
            select(
                Tags.name,
                func.count(),
            )
            .join(
                QuestionTags,
                QuestionTags.tag_id == Tags.id,
            )
            .join(
                Questions,
                Questions.id == QuestionTags.question_id,
            )
            .group_by(Tags.name)
        )

        if level is not None:
            level_query = level_query.where(Questions.level == level)
            question_type_query = question_type_query.where(
                Questions.level == level
            )
            tag_query = tag_query.where(Questions.level == level)

        return {
            "levels": dict(session.exec(level_query).all()),
            "question_types": dict(session.exec(question_type_query).all()),
            "tags": dict(session.exec(tag_query).all()),
        }



def statistics(
    db: DatabaseManagerDep,
    current_user: User,
    period: str = "all",
    level: str = "all",  # "all", "N4", "N5"
) -> dict[str, object]:
    if not(question_utils.validate_period(period)):
        return {"invalid_period": period}

    # summary
    streak = get_user_streak(db, current_user)
    correct, incorrect = get_period_statistics(db, current_user, period, level)
    answered = correct + incorrect
    accuracy = (correct / answered) * 100 if answered > 0 else 0
    accuracy = int(accuracy)

    # skills (question_types)
    skills : list[dict[str, object]] = get_question_type_statistics(db,
                                            current_user,
                                            period,
                                            level)

    # skillTags
    skillTags = get_skill_tag_statistics(db, current_user, period, level)

    # timeline
    timeline = get_user_timeline(db, current_user, period, level)

    # database info
    db_info = get_database_statistics(db, level)

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
