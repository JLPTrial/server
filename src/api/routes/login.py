from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response

from ...core.firebase.initialization import FirebaseTokenError
from ...core.firebase.operations import (
    create_firebase_session_cookie,
    get_firebase_user_profile,
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
    get_identity_from_session_cookie,
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
    identity = signup_user(db, credentials)
    session_cookie = create_firebase_session_cookie(credentials.uid_token)
    set_session_cookie(response, session_cookie)

    name = credentials.name.strip() or identity.name or identity.email.split("@")[0]
    return {
        "user": {
            "firebase_uid": identity.uid,
            "email": identity.email,
            "name": name,
        },
    }


@router.post("/login", responses={401: {"description": "Invalid credentials"}})
def login(
    response: Response, db: DatabaseManagerDep, credentials: FirebaseLoginRequest
) -> Any:
    try:
        identity = login_user(db, credentials)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    session_cookie = create_firebase_session_cookie(credentials.uid_token)
    set_session_cookie(response, session_cookie)
    return {
        "user": {
            "firebase_uid": identity.uid,
            "email": identity.email,
            "name": identity.name,
        },
    }


@router.post(
    "/refresh",
    responses={
        401: {"description": "Invalid refresh token"},
        404: {"description": "User not found"},
    },
)
def refresh(request: Request, db: DatabaseManagerDep) -> Any:
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_cookie:
        raise HTTPException(status_code=401, detail=INVALID_SESSION_COOKIE_MESSAGE)

    try:
        identity = get_identity_from_session_cookie(db, session_cookie)

        profile = get_firebase_user_profile(identity.uid)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "user": {
            "firebase_uid": profile.uid,
            "email": profile.email,
            "name": profile.name,
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
