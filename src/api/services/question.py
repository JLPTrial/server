from ...core.config import settings
from ...models.question import Questions, Tags, UserQuestion


def get_available_question_databases_ids():
    return list(settings.AVAILABLE_QUESTION_DATABASES.values())


# Validations
def validate_question_database_id(database_id: int) -> bool:
    return database_id in settings.AVAILABLE_QUESTION_DATABASES.values()


def validate_question_topic(topic: str) -> bool:
    return topic in settings.AVAILABLE_QUESTION_TOPICS


# Filters
def add_filter_question_id(stmt, question_id: int):
    if question_id:
        return stmt.where(Questions.id == question_id)
    return stmt


def add_filter_topic(stmt, topic: str):
    if topic:
        return stmt.where(Questions.question_type == topic)
    return stmt


def add_filter_tag(stmt, tag: str):
    if tag:
        return stmt.join(Questions.tags).where(Tags.name.ilike(f"%{tag}%"))
    return stmt


def add_filter_answered(stmt, answered: str, user_firebase_uid: str):
    if answered.lower() == "true":
        return stmt.outerjoin(Questions.users_link).where(
            (UserQuestion.user_firebase_uid == user_firebase_uid)
            & (UserQuestion.status == "answered")
        )
    elif answered.lower() == "false":
        return stmt.outerjoin(Questions.users_link).where(
            (UserQuestion.user_firebase_uid != user_firebase_uid)
            | (UserQuestion.status != "answered")
        )

    return stmt
