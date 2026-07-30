from collections.abc import Callable
from datetime import timedelta
from typing import Any, TypeVar, cast

from firebase_admin import auth as firebase_auth

from ..config import settings
from .constants import (
    CERTIFICATE_FETCH_MESSAGE,
    CONFIGURATION_NOT_FOUND_MESSAGE,
    EXPIRED_SESSION_COOKIE_MESSAGE,
    EXPIRED_TOKEN_MESSAGE,
    FIREBASE_USER_NOT_FOUND_MESSAGE,
    INVALID_SESSION_COOKIE_MESSAGE,
    INVALID_TOKEN_MESSAGE,
    REVOKED_SESSION_COOKIE_MESSAGE,
    REVOKED_TOKEN_MESSAGE,
    SESSION_COOKIE_SIGN_ERROR_MESSAGE,
    UNEXPECTED_RESPONSE_MESSAGE,
    USER_DISABLED_MESSAGE,
)
from .initialization import FirebaseIdentity, FirebaseTokenError, get_firebase_app

T = TypeVar("T")
FirebaseErrorMap = dict[type[Exception], str]

FIREBASE_ID_TOKEN_ERRORS: FirebaseErrorMap = {
    firebase_auth.InvalidIdTokenError: INVALID_TOKEN_MESSAGE,
    firebase_auth.ExpiredIdTokenError: EXPIRED_TOKEN_MESSAGE,
    firebase_auth.RevokedIdTokenError: REVOKED_TOKEN_MESSAGE,
    firebase_auth.UserDisabledError: USER_DISABLED_MESSAGE,
    firebase_auth.CertificateFetchError: CERTIFICATE_FETCH_MESSAGE,
    firebase_auth.ConfigurationNotFoundError: CONFIGURATION_NOT_FOUND_MESSAGE,
    firebase_auth.UnexpectedResponseError: UNEXPECTED_RESPONSE_MESSAGE,
}

FIREBASE_SESSION_COOKIE_ERRORS: FirebaseErrorMap = {
    firebase_auth.InvalidSessionCookieError: INVALID_SESSION_COOKIE_MESSAGE,
    firebase_auth.ExpiredSessionCookieError: EXPIRED_SESSION_COOKIE_MESSAGE,
    firebase_auth.RevokedSessionCookieError: REVOKED_SESSION_COOKIE_MESSAGE,
    firebase_auth.UserDisabledError: USER_DISABLED_MESSAGE,
    firebase_auth.CertificateFetchError: CERTIFICATE_FETCH_MESSAGE,
    firebase_auth.ConfigurationNotFoundError: CONFIGURATION_NOT_FOUND_MESSAGE,
    firebase_auth.UnexpectedResponseError: UNEXPECTED_RESPONSE_MESSAGE,
}

FIREBASE_GET_USER_ERRORS: FirebaseErrorMap = {
    firebase_auth.UserNotFoundError: FIREBASE_USER_NOT_FOUND_MESSAGE,
    firebase_auth.ConfigurationNotFoundError: CONFIGURATION_NOT_FOUND_MESSAGE,
    firebase_auth.UnexpectedResponseError: UNEXPECTED_RESPONSE_MESSAGE,
}

FIREBASE_SESSION_COOKIE_SIGN_ERRORS: FirebaseErrorMap = {
    firebase_auth.InvalidIdTokenError: INVALID_TOKEN_MESSAGE,
    firebase_auth.ExpiredIdTokenError: EXPIRED_TOKEN_MESSAGE,
    firebase_auth.RevokedIdTokenError: REVOKED_TOKEN_MESSAGE,
    firebase_auth.UserDisabledError: USER_DISABLED_MESSAGE,
    firebase_auth.CertificateFetchError: CERTIFICATE_FETCH_MESSAGE,
    firebase_auth.ConfigurationNotFoundError: CONFIGURATION_NOT_FOUND_MESSAGE,
    firebase_auth.TokenSignError: SESSION_COOKIE_SIGN_ERROR_MESSAGE,
    firebase_auth.UnexpectedResponseError: UNEXPECTED_RESPONSE_MESSAGE,
}


def _identity_from_claims(claims: dict[str, Any]) -> FirebaseIdentity:
    email = claims.get("email")
    if not email:
        raise FirebaseTokenError("Firebase token does not include an email")

    uid = claims.get("uid") or claims.get("sub") or claims.get("user_id")
    if not uid:
        raise FirebaseTokenError("Firebase token does not include a user id")

    return FirebaseIdentity(uid=str(uid), email=str(email), name=claims.get("name"))


def _run_firebase_operation(
    operation: Callable[[], T], error_map: FirebaseErrorMap
) -> T:
    try:
        return operation()
    except tuple(error_map) as exc:
        raise FirebaseTokenError(error_map[type(exc)]) from exc


def verify_firebase_id_token(id_token: str) -> FirebaseIdentity:
    claims = _run_firebase_operation(
        lambda: firebase_auth.verify_id_token(id_token, app=get_firebase_app()),
        FIREBASE_ID_TOKEN_ERRORS,
    )

    return _identity_from_claims(cast(dict[str, Any], claims))


def create_firebase_session_cookie(id_token: str) -> str:
    cookie: str = _run_firebase_operation(
        lambda: firebase_auth.create_session_cookie(
            id_token,
            expires_in=timedelta(days=settings.FIREBASE_SESSION_COOKIE_EXPIRE_DAYS),
            app=get_firebase_app(),
        ),
        FIREBASE_SESSION_COOKIE_SIGN_ERRORS,
    )

    return cookie


def verify_firebase_session_cookie(session_cookie: str) -> FirebaseIdentity:
    claims = _run_firebase_operation(
        lambda: firebase_auth.verify_session_cookie(
            session_cookie,
            check_revoked=True,
            app=get_firebase_app(),
        ),
        FIREBASE_SESSION_COOKIE_ERRORS,
    )

    return _identity_from_claims(cast(dict[str, Any], claims))


def get_firebase_user_profile(uid: str) -> FirebaseIdentity:
    record = _run_firebase_operation(
        lambda: firebase_auth.get_user(uid, app=get_firebase_app()),
        FIREBASE_GET_USER_ERRORS,
    )

    if not record.email:
        raise FirebaseTokenError("Firebase user does not include an email")

    return FirebaseIdentity(
        uid=record.uid,
        email=str(record.email),
        name=record.display_name,
    )


def revoke_firebase_sessions(uid: str) -> None:
    firebase_auth.revoke_refresh_tokens(uid, app=get_firebase_app())
