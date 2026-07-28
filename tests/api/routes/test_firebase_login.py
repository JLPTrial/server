from fastapi.testclient import TestClient
from sqlmodel import select

from src.api.routes import login as login_routes
from src.api.utils.cookies import SESSION_COOKIE_NAME
from src.core.config import settings
from src.core.firebase.initialization import FirebaseIdentity
from src.models import User


def _firebase_identity(uid: str, email: str, name: str | None = None) -> FirebaseIdentity:
	return FirebaseIdentity(uid=uid, email=email, name=name)


def test_firebase_signup_creates_local_user(client: TestClient, db, monkeypatch) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)
	monkeypatch.setattr(
		"src.api.services.login.resolve_signup_identity",
		lambda uid_token: _firebase_identity("firebase-uid-123", "fulano@jlptrial.com", "Fulano"),
	)
	monkeypatch.setattr(
		login_routes,
		"build_session_cookie",
		lambda identity, uid_token: "firebase-session-cookie",
	)

	response = client.post(
		"/users/signup",
		json={"uid_token": "firebase-id-token", "name": "Fulano"},
	)

	assert response.status_code == 200
	body = response.json()
	assert body == {
		"user": {
			"firebase_uid": "firebase-uid-123",
			"email": "fulano@jlptrial.com",
			"name": "Fulano",
		},
	}
	assert SESSION_COOKIE_NAME in response.headers.get("set-cookie", "")
	assert response.cookies.get(SESSION_COOKIE_NAME) == "firebase-session-cookie"

	stored_user = db.exec(
		select(User).where(User.firebase_uid == "firebase-uid-123")
	).first()
	assert stored_user is not None


def test_firebase_login_auto_registers_unknown_user(
	client: TestClient, db, monkeypatch
) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)
	monkeypatch.setattr(
		"src.api.services.login.resolve_login_identity",
		lambda uid_token: _firebase_identity("firebase-uid-456", "missing@jlptrial.com", "Missing"),
	)
	monkeypatch.setattr(
		login_routes,
		"build_session_cookie",
		lambda identity, uid_token: "firebase-session-cookie",
	)

	response = client.post("/users/login", json={"uid_token": "firebase-id-token"})

	assert response.status_code == 200
	assert response.json()["user"]["firebase_uid"] == "firebase-uid-456"

	stored_user = db.exec(
		select(User).where(User.firebase_uid == "firebase-uid-456")
	).first()
	assert stored_user is not None


def test_firebase_login_sets_session_cookie(client: TestClient, db, monkeypatch) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)
	db.add(User(firebase_uid="firebase-uid-789"))
	db.commit()

	monkeypatch.setattr(
		"src.api.services.login.resolve_login_identity",
		lambda uid_token: _firebase_identity("firebase-uid-789", "active@jlptrial.com", "Active User"),
	)
	monkeypatch.setattr(
		login_routes,
		"build_session_cookie",
		lambda identity, uid_token: "firebase-session-cookie",
	)

	response = client.post("/users/login", json={"uid_token": "firebase-id-token"})

	assert response.status_code == 200
	assert response.json() == {
		"user": {
			"firebase_uid": "firebase-uid-789",
			"email": "active@jlptrial.com",
			"name": "Active User",
		},
	}
	assert response.cookies.get(SESSION_COOKIE_NAME) == "firebase-session-cookie"


def test_firebase_refresh_reads_session_cookie(client: TestClient, db, monkeypatch) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)
	monkeypatch.setattr(
		"src.api.services.login.resolve_session_identity",
		lambda session_cookie: _firebase_identity("firebase-uid-111", "refresh@jlptrial.com", "Refresh User"),
	)

	client.cookies.set(SESSION_COOKIE_NAME, "firebase-session-cookie", path="/")
	response = client.post("/users/refresh")
	client.cookies.clear()

	assert response.status_code == 200
	assert response.json() == {
		"user": {
			"firebase_uid": "firebase-uid-111",
			"email": "refresh@jlptrial.com",
			"name": "Refresh User",
		},
	}

	stored_user = db.exec(
		select(User).where(User.firebase_uid == "firebase-uid-111")
	).first()
	assert stored_user is not None


def test_firebase_logout_clears_session_cookie(client: TestClient, monkeypatch) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", True)
	called = {}

	def fake_revoke(uid: str) -> None:
		called["uid"] = uid

	monkeypatch.setattr(
		login_routes,
		"revoke_session",
		lambda session_cookie: fake_revoke("firebase-uid-222"),
	)

	client.cookies.set(SESSION_COOKIE_NAME, "firebase-session-cookie", path="/")
	response = client.post("/users/logout")
	client.cookies.clear()

	assert response.status_code == 200
	assert response.json() == {"message": "Logged out"}
	assert called["uid"] == "firebase-uid-222"
	assert SESSION_COOKIE_NAME in response.headers.get("set-cookie", "")


def test_dev_auth_flow_skips_firebase(client: TestClient, db, monkeypatch) -> None:
	monkeypatch.setattr(settings, "SECURE_REQUEST", False)

	signup_response = client.post(
		"/users/signup",
		json={"uid_token": "unused-token", "name": "  Dev User  "},
	)

	assert signup_response.status_code == 200
	assert signup_response.json() == {
		"user": {
			"firebase_uid": "__dev__",
			"email": "dev@jlptrial.local",
			"name": "Dev User",
		},
	}
	assert signup_response.cookies.get(SESSION_COOKIE_NAME) == "__dev__"

	refresh_response = client.post("/users/refresh")

	assert refresh_response.status_code == 200
	assert refresh_response.json() == {
		"user": {
			"firebase_uid": "__dev__",
			"email": "dev@jlptrial.local",
			"name": None,
		},
	}

	logout_response = client.post("/users/logout")

	assert logout_response.status_code == 200
	assert logout_response.json() == {"message": "Logged out"}
	assert SESSION_COOKIE_NAME in logout_response.headers.get("set-cookie", "")
