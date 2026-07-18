from ..config import settings
from ...models import FirebaseLoginRequest, FirebaseSignupRequest
from .initialization import FirebaseIdentity, FirebaseTokenError
from .operations import (
    create_firebase_session_cookie,
    get_firebase_user_profile,
    revoke_firebase_sessions,
    verify_firebase_id_token,
    verify_firebase_session_cookie,
)

DEV_FIREBASE_UID = "__dev__"
DEV_FIREBASE_EMAIL = "dev@jlptrial.local"

INVALID_UID_TOKEN_MESSAGE = "Invalid uid token"  # nosec B105
INVALID_SESSION_COOKIE_MESSAGE = "Invalid Firebase session cookie"  # nosec B105


def _get_dev_identity(name: str | None = None) -> FirebaseIdentity:
    return FirebaseIdentity(uid=DEV_FIREBASE_UID, email=DEV_FIREBASE_EMAIL, name=name)


def resolve_signup_identity(credentials: FirebaseSignupRequest) -> FirebaseIdentity:
    if not settings.SECURE_REQUEST:
        return _get_dev_identity(credentials.name.strip() or None)

    try:
        return verify_firebase_id_token(credentials.uid_token)
    except FirebaseTokenError as exc:
        raise ValueError(INVALID_UID_TOKEN_MESSAGE) from exc


def resolve_login_identity(credentials: FirebaseLoginRequest) -> FirebaseIdentity:
    if not settings.SECURE_REQUEST:
        return _get_dev_identity()

    try:
        return verify_firebase_id_token(credentials.uid_token)
    except FirebaseTokenError as exc:
        raise ValueError(INVALID_UID_TOKEN_MESSAGE) from exc


def resolve_session_identity(session_cookie: str) -> FirebaseIdentity:
    if not settings.SECURE_REQUEST:
        return _get_dev_identity()

    try:
        identity = verify_firebase_session_cookie(session_cookie)
    except FirebaseTokenError as exc:
        raise ValueError(INVALID_SESSION_COOKIE_MESSAGE) from exc

    return get_firebase_user_profile(identity.uid)


def build_session_cookie(identity: FirebaseIdentity, uid_token: str) -> str:
    if not settings.SECURE_REQUEST:
        return identity.uid

    return create_firebase_session_cookie(uid_token)


def revoke_session(session_cookie: str | None) -> None:
    if not settings.SECURE_REQUEST or not session_cookie:
        return

    try:
        identity = verify_firebase_session_cookie(session_cookie)
    except FirebaseTokenError:
        return

    revoke_firebase_sessions(identity.uid)
