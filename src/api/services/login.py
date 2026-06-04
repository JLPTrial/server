from sqlmodel import select

from ...core.firebase.initialization import FirebaseTokenError
from ...core.firebase.operations import (
    verify_firebase_id_token,
    verify_firebase_session_cookie,
)
from ...database.session import SessionDep
from ...models import FirebaseLoginRequest, FirebaseSignupRequest, User

INVALID_UID_TOKEN_MESSAGE = "Invalid uid token"  # nosec B105
INVALID_SESSION_COOKIE_MESSAGE = "Invalid Firebase session cookie"  # nosec B105
USER_NOT_REGISTERED_MESSAGE = "User is not registered"  # nosec B105
USER_NOT_FOUND_MESSAGE = "User not found"  # nosec B105


def signup_user(session: SessionDep, credentials: FirebaseSignupRequest) -> User:
    try:
        identity = verify_firebase_id_token(credentials.uid_token)
    except FirebaseTokenError as exc:
        raise ValueError(INVALID_UID_TOKEN_MESSAGE) from exc

    user = _get_user_by_firebase_uid(session, identity.uid)

    if user is None:
        user = session.exec(select(User).where(User.email == identity.email)).first()

    name = credentials.name.strip() or identity.name or identity.email.split("@")[0]

    if user:
        user.firebase_uid = identity.uid
        user.email = identity.email
        user.name = name
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

    user = User(
        firebase_uid=identity.uid,
        email=identity.email,
        name=name,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def login_user(session: SessionDep, credentials: FirebaseLoginRequest) -> User:
    try:
        identity = verify_firebase_id_token(credentials.uid_token)
    except FirebaseTokenError as exc:
        raise ValueError(INVALID_UID_TOKEN_MESSAGE) from exc

    user = _get_user_by_firebase_uid(session, identity.uid)
    if not user:
        raise LookupError(USER_NOT_REGISTERED_MESSAGE)

    return user


def get_user_from_session_cookie(session: SessionDep, session_cookie: str) -> User:
    try:
        identity = verify_firebase_session_cookie(session_cookie)
    except FirebaseTokenError as exc:
        raise ValueError(INVALID_SESSION_COOKIE_MESSAGE) from exc

    user = _get_user_by_firebase_uid(session, identity.uid)
    if not user:
        raise LookupError(USER_NOT_FOUND_MESSAGE)

    return user


def _get_user_by_firebase_uid(session: SessionDep, firebase_uid: str) -> User | None:
    return session.exec(select(User).where(User.firebase_uid == firebase_uid)).first()
