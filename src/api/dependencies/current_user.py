from fastapi import HTTPException, Request, status
from sqlmodel import select

from ...api.services.login import get_user_from_session_cookie
from ...core.config import settings
from ...core.firebase.authentication import DEV_FIREBASE_UID
from ...core.firebase.constants import INVALID_SESSION_COOKIE_MESSAGE
from ...database.session import DatabaseManagerDep
from ...models import User
from ..utils.cookies import SESSION_COOKIE_NAME

# Esta parte é a principal responsável por fazer a autorização
# do usuário ao banco, em princípio, é o que permite que novas
# funcionalidades de acesso sejam feitas sem se preocupar com
# autenticação ou coisas do tipo


def get_current_user(request: Request, db: DatabaseManagerDep) -> User:
    if not settings.SECURE_REQUEST:
        return get_dummy_user(db)
    return get_firebase_user(request, db)


def get_dummy_user(db: DatabaseManagerDep) -> User:
    with db.session() as session:
        user = session.exec(
            select(User).where(User.firebase_uid == DEV_FIREBASE_UID)
        ).first()
        if user:
            return user

        test_user = User(firebase_uid=DEV_FIREBASE_UID)
        session.add(test_user)
        session.commit()
        session.refresh(test_user)
        return test_user


def get_firebase_user(request: Request, db: DatabaseManagerDep) -> User:
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_SESSION_COOKIE_MESSAGE,
        )

    try:
        return get_user_from_session_cookie(db, session_cookie)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_SESSION_COOKIE_MESSAGE,
        ) from exc
