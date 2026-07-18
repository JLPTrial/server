from sqlmodel import Session, select

from ...core.firebase.authentication import (
    resolve_login_identity,
    resolve_session_identity,
    resolve_signup_identity,
)
from ...core.firebase.initialization import FirebaseIdentity
from ...database.session import DatabaseManagerDep
from ...models import FirebaseLoginRequest, FirebaseSignupRequest, User


def signup_user(
    db: DatabaseManagerDep, credentials: FirebaseSignupRequest
) -> FirebaseIdentity:
    identity = resolve_signup_identity(credentials)

    _get_local_user(db, identity.uid)
    return identity


def login_user(
    db: DatabaseManagerDep, credentials: FirebaseLoginRequest
) -> FirebaseIdentity:
    identity = resolve_login_identity(credentials)

    _get_local_user(db, identity.uid)
    return identity


def get_identity_from_session_cookie(
    db: DatabaseManagerDep, session_cookie: str
) -> FirebaseIdentity:
    identity = resolve_session_identity(session_cookie)

    _get_local_user(db, identity.uid)
    return identity


def get_user_from_session_cookie(db: DatabaseManagerDep, session_cookie: str) -> User:
    identity = get_identity_from_session_cookie(db, session_cookie)
    return User(firebase_uid=identity.uid)


def _get_local_user(db: DatabaseManagerDep, firebase_uid: str) -> None:
    with db.session() as session:
        if _get_user_by_firebase_uid(session, firebase_uid) is None:
            session.add(User(firebase_uid=firebase_uid))
            session.commit()


def _get_user_by_firebase_uid(session: Session, firebase_uid: str) -> User | None:
    return session.exec(select(User).where(User.firebase_uid == firebase_uid)).first()
