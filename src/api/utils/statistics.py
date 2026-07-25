from ...core.config import settings


def wrap_statistics_output(
        **kwargs: dict[str, object]
) -> dict[str, object]:
    return {
        "summary":{
            "answered": kwargs.get("answered", 0),
            "correct": kwargs.get("correct", 0),
            "incorrect": kwargs.get("incorrect", 0),
            "accuracy": kwargs.get("accuracy", 0.0),
            "streak": kwargs.get("streak", 0)
        },
        "skills": kwargs.get("skills", []),
        "skillTags": kwargs.get("skillTags", {}),
        "timeline": kwargs.get("timeline", []),
        "database": kwargs.get("database", {})
    }

def validate_question_level(level: str | None) -> str | None:
    if level in settings.AVAILABLE_QUESTION_LEVELS.values():
        return level
    else:
        return None
