from datetime import timedelta

from fastapi import Response

from ...core.config import settings

SESSION_COOKIE_NAME = "firebase_session"


def set_session_cookie(response: Response, session_cookie: str) -> None:
    valid_time = int(
        timedelta(days=settings.FIREBASE_SESSION_COOKIE_EXPIRE_DAYS).total_seconds()
    )
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_cookie,
        httponly=True,
        secure=settings.IS_PROD,
        samesite="lax",
        max_age=valid_time,
        expires=valid_time,
        path="/",
    )


def delete_session_cookie(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME)
