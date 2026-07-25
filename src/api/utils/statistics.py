from ...core.config import settings


def validate_question_level(level: str | None) -> str | None:
    if level in settings.AVAILABLE_QUESTION_LEVELS.values():
        return level
    else:
        return None
