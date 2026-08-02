
import calendar
from collections import OrderedDict
from datetime import UTC, datetime, timedelta

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


def period_to_start_date(period: str) -> datetime | None:
    now = datetime.now(UTC)

    if period == "all":
        return None

    if period == "day":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "week":
        monday = now - timedelta(days=now.weekday())
        return monday.replace(hour=0, minute=0, second=0, microsecond=0)

    if period == "month":
        return now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    if period == "year":
        return now.replace(
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

    raise ValueError(f"Invalid period: {period}")

def get_timeline_bucket(date: datetime, period: str) -> str:
    if period == "day":
        return date.strftime("%Y-%m-%d")

    if period == "week":
        return date.strftime("%Y-%m-%d")

    if period == "month":
        year, week, _ = date.isocalendar()
        return f"{year}-W{week:02d}"

    if period == "year":
        return date.strftime("%Y-%m")

    if period == "all":
        return date.strftime("%Y")

    raise ValueError(f"Invalid period: {period}")

def get_empty_timeline(period: str) -> OrderedDict[str, dict[str, int]]:
    today = datetime.now(UTC).date()

    buckets: OrderedDict[str, dict[str, int]] = OrderedDict()

    if period == "day":
        buckets[today.strftime("%Y-%m-%d")] = {
            "correct": 0,
            "incorrect": 0,
        }

    elif period == "week":
        # Monday -> Sunday of the current week
        monday = today - timedelta(days=today.weekday())

        for i in range(7):
            day = monday + timedelta(days=i)
            buckets[day.strftime("%Y-%m-%d")] = {
                "correct": 0,
                "incorrect": 0,
            }

    elif period == "month":
        # Every ISO week that intersects the current calendar month
        first_day = today.replace(day=1)
        last_day = today.replace(
            day=calendar.monthrange(today.year, today.month)[1]
        )

        current = first_day
        while current <= last_day:
            iso_year, iso_week, _ = current.isocalendar()
            bucket = f"{iso_year}-W{iso_week:02d}"

            buckets.setdefault(bucket, {
                "correct": 0,
                "incorrect": 0,
            })

            current += timedelta(days=1)

    elif period == "year":
        for month in range(1, 13):
            buckets[f"{today.year}-{month:02d}"] = {
                "correct": 0,
                "incorrect": 0,
            }

    elif period == "all":
        for year in range(2026, today.year + 1):
            buckets[str(year)] = {
                "correct": 0,
                "incorrect": 0,
            }

    else:
        raise ValueError(f"Invalid period: {period}")

    return buckets
