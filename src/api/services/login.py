from sqlmodel import Session, select

from ...core.firebase.initialization import FirebaseIdentity, FirebaseTokenError
from ...core.firebase.operations import (
    verify_firebase_id_token,
    verify_firebase_session_cookie,
)
from ...database.session import DatabaseManagerDep
from ...models import FirebaseLoginRequest, FirebaseSignupRequest, User

INVALID_UID_TOKEN_MESSAGE = "Invalid uid token"  # nosec B105
INVALID_SESSION_COOKIE_MESSAGE = "Invalid Firebase session cookie"  # nosec B105
USER_NOT_REGISTERED_MESSAGE = "User is not registered"  # nosec B105
USER_NOT_FOUND_MESSAGE = "User not found"  # nosec B105


def signup_user(
    db: DatabaseManagerDep, credentials: FirebaseSignupRequest
) -> FirebaseIdentity:
    try:
        identity = verify_firebase_id_token(credentials.uid_token)
    except FirebaseTokenError as exc:
        raise ValueError(INVALID_UID_TOKEN_MESSAGE) from exc

    with db.session() as session:
        user = _get_user_by_firebase_uid(session, identity.uid)
        if user is None:
            session.add(User(firebase_uid=identity.uid))
            session.commit()

    return identity


def login_user(
    db: DatabaseManagerDep, credentials: FirebaseLoginRequest
) -> FirebaseIdentity:
    try:
        identity = verify_firebase_id_token(credentials.uid_token)
    except FirebaseTokenError as exc:
        raise ValueError(INVALID_UID_TOKEN_MESSAGE) from exc

    with db.session() as session:
        if _get_user_by_firebase_uid(session, identity.uid) is None:
            raise LookupError(USER_NOT_REGISTERED_MESSAGE)

    return identity


def get_identity_from_session_cookie(
    db: DatabaseManagerDep, session_cookie: str
) -> FirebaseIdentity:
    try:
        identity = verify_firebase_session_cookie(session_cookie)
    except FirebaseTokenError as exc:
        raise ValueError(INVALID_SESSION_COOKIE_MESSAGE) from exc

    with db.session() as session:
        if _get_user_by_firebase_uid(session, identity.uid) is None:
            raise LookupError(USER_NOT_FOUND_MESSAGE)

    return identity


def get_user_from_session_cookie(db: DatabaseManagerDep, session_cookie: str) -> User:
    identity = get_identity_from_session_cookie(db, session_cookie)
    return User(firebase_uid=identity.uid)


def _get_user_by_firebase_uid(session: Session, firebase_uid: str) -> User | None:
    return session.exec(select(User).where(User.firebase_uid == firebase_uid)).first()
