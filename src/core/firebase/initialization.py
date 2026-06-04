import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, cast

import firebase_admin
from firebase_admin import credentials

from ..config import settings


@dataclass(frozen=True)
class FirebaseIdentity:
    uid: str
    email: str
    name: str | None = None


class FirebaseTokenError(ValueError):
    pass


# Talvez isto fique um pouco confuso
# Mas é o mais perto que chego de implementar um singleton em Python
# A ideia é ter um objeto público criável apenas uma vez mas com acesso que parece estático.


@lru_cache(maxsize=1)
def load_service_account() -> dict[str, Any]:
    service_account_path = Path(settings.FIREBASE_SERVICE_ACCOUNT_FILE)
    if not service_account_path.exists():
        raise FirebaseTokenError("Firebase service account file was not found")
    return cast(dict[str, Any], json.loads(service_account_path.read_text()))


@lru_cache(maxsize=1)
def get_firebase_app() -> firebase_admin.App:
    service_account = load_service_account()
    project_id = service_account.get("project_id")
    if not project_id:
        raise FirebaseTokenError("Firebase project id is missing from service account")

    try:
        return firebase_admin.get_app()
    except ValueError:
        pass

    service_account_path = Path(settings.FIREBASE_SERVICE_ACCOUNT_FILE)
    try:
        return firebase_admin.initialize_app(
            credentials.Certificate(str(service_account_path)),
            {"projectId": str(project_id)},
        )
    except ValueError as exc:
        raise FirebaseTokenError("Firebase app could not be initialized") from exc
