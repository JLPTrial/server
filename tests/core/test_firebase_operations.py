from types import SimpleNamespace

import pytest
from firebase_admin import auth as firebase_auth

from src.core.firebase import operations
from src.core.firebase.constants import FIREBASE_USER_NOT_FOUND_MESSAGE
from src.core.firebase.initialization import FirebaseTokenError


def test_get_firebase_user_profile_returns_identity(monkeypatch) -> None:
	record = SimpleNamespace(
		uid="firebase-uid-123",
		email="fulano@jlptrial.com",
		display_name="Fulano",
	)
	monkeypatch.setattr(operations, "get_firebase_app", lambda: None)
	monkeypatch.setattr(firebase_auth, "get_user", lambda uid, app: record)

	identity = operations.get_firebase_user_profile("firebase-uid-123")

	assert identity.uid == "firebase-uid-123"
	assert identity.email == "fulano@jlptrial.com"
	assert identity.name == "Fulano"


def test_get_firebase_user_profile_user_not_found(monkeypatch) -> None:
	def raise_not_found(uid, app):
		raise firebase_auth.UserNotFoundError("no user")

	monkeypatch.setattr(operations, "get_firebase_app", lambda: None)
	monkeypatch.setattr(firebase_auth, "get_user", raise_not_found)

	with pytest.raises(FirebaseTokenError, match=FIREBASE_USER_NOT_FOUND_MESSAGE):
		operations.get_firebase_user_profile("missing-uid")


def test_get_firebase_user_profile_requires_email(monkeypatch) -> None:
	record = SimpleNamespace(uid="firebase-uid-123", email=None, display_name=None)
	monkeypatch.setattr(operations, "get_firebase_app", lambda: None)
	monkeypatch.setattr(firebase_auth, "get_user", lambda uid, app: record)

	with pytest.raises(FirebaseTokenError, match="does not include an email"):
		operations.get_firebase_user_profile("firebase-uid-123")
