from typing import Annotated

from fastapi import APIRouter, Depends

from ...api.dependencies.current_user import get_current_user
from ...database.session import DatabaseManagerDep
from ...models import User
from ...models.statistic_response import StatisticsResponse
from ..services import statistics as statistics_services

router = APIRouter(tags=["statistics"])


# Statistics
@router.get(
    "/statistics",
    response_model=StatisticsResponse,
)
def read_statistics(
    db: DatabaseManagerDep,
    current_user: Annotated[User, Depends(get_current_user)],
    period: str = "all",  # "all", "day", "week", "month", "year"
    level: str = "all",  # "all", "N4", "N5"
) -> dict[str, object]:
    return statistics_services.statistics(
        db=db, current_user=current_user, period=period, level=level
    )
