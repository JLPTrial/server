from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response

from ...core.firebase.initialization import FirebaseTokenError
from ...core.firebase.operations import (
    create_firebase_session_cookie,
    revoke_firebase_sessions,
    verify_firebase_session_cookie,
)
from ...database.session import DatabaseManagerDep
from ...models import (
    FirebaseLoginRequest,
    FirebaseSignupRequest,
)
from ..services.login import (
    INVALID_SESSION_COOKIE_MESSAGE,
    get_user_from_session_cookie,
    login_user,
    signup_user,
)
from ..utils.cookies import (
    SESSION_COOKIE_NAME,
    delete_session_cookie,
    set_session_cookie,
)

router = APIRouter(prefix="/users", tags=["login"])


@router.post(
    "/signup",
    responses={401: {"description": "Invalid credentials"}},
)
def signup(
    response: Response, db: DatabaseManagerDep, credentials: FirebaseSignupRequest
) -> Any:
    with db.session("users") as session:
        user = signup_user(session, credentials)
        session_cookie = create_firebase_session_cookie(credentials.uid_token)
        set_session_cookie(response, session_cookie)
        return {
            "user": {
                "firebase_uid": user.firebase_uid,
                "email": user.email,
                "name": user.name,
            },
        }


@router.post("/login", responses={401: {"description": "Invalid credentials"}})
def login(
    response: Response, 
    db: DatabaseManagerDep, 
    credentials: FirebaseLoginRequest
) -> Any:
    with db.session("users") as session:
        try:
            user = login_user(session, credentials)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except LookupError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

        session_cookie = create_firebase_session_cookie(credentials.uid_token)
        set_session_cookie(response, session_cookie)
        return {
            "user": {
                "firebase_uid": user.firebase_uid,
                "email": user.email,
                "name": user.name,
            },
        }


@router.post(
    "/refresh",
    responses={
        401: {"description": "Invalid refresh token"},
        404: {"description": "User not found"},
    },
)
def refresh(request: Request, 
            db: DatabaseManagerDep) -> Any:
    
    with db.session("users") as session:
        session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
        if not session_cookie:
            raise HTTPException(status_code=401, detail=INVALID_SESSION_COOKIE_MESSAGE)

        try:
            user = get_user_from_session_cookie(session, session_cookie)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

        return {
            "user": {
                "firebase_uid": user.firebase_uid,
                "email": user.email,
                "name": user.name,
            },
        }


@router.post("/logout")
def logout(response: Response, request: Request) -> dict[str, str]:
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if session_cookie:
        identity = None
        try:
            identity = verify_firebase_session_cookie(session_cookie)
        except FirebaseTokenError:
            identity = None

        if identity is not None:
            revoke_firebase_sessions(identity.uid)
    delete_session_cookie(response)
    return {"message": "Logged out"}
