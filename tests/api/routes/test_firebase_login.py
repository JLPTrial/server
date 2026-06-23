from fastapi.testclient import TestClient
from sqlmodel import select

from src.api.routes import login as login_routes
from src.api.utils.cookies import SESSION_COOKIE_NAME
from src.core.firebase.initialization import FirebaseIdentity
from src.models import User


def _firebase_identity(uid: str, email: str, name: str | None = None) -> FirebaseIdentity:
	return FirebaseIdentity(uid=uid, email=email, name=name)


def test_firebase_signup_creates_local_user(client: TestClient, db, monkeypatch) -> None:
	monkeypatch.setattr(
		"src.api.services.login.verify_firebase_id_token",
		lambda uid_token: _firebase_identity("firebase-uid-123", "fulano@jlptrial.com", "Fulano"),
	)
	monkeypatch.setattr(
		login_routes,
		"create_firebase_session_cookie",
		lambda uid_token: "firebase-session-cookie",
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
		select(User).where(User.email == "fulano@jlptrial.com")
	).first()
	assert stored_user is not None
	assert stored_user.name == "Fulano"
	assert stored_user.firebase_uid == "firebase-uid-123"


def test_firebase_login_requires_registered_user(client: TestClient, monkeypatch) -> None:
	monkeypatch.setattr(
		"src.api.services.login.verify_firebase_id_token",
		lambda uid_token: _firebase_identity("firebase-uid-456", "missing@jlptrial.com", "Missing"),
	)

	response = client.post("/users/login", json={"uid_token": "firebase-id-token"})

	assert response.status_code == 401
	assert response.json()["detail"] == "User is not registered"


def test_firebase_login_sets_session_cookie(client: TestClient, db, monkeypatch) -> None:
	db.add(
		User(
			firebase_uid="firebase-uid-789",
			email="active@jlptrial.com",
			name="Active User",
		)
	)
	db.commit()

	monkeypatch.setattr(
		"src.api.services.login.verify_firebase_id_token",
		lambda uid_token: _firebase_identity("firebase-uid-789", "active@jlptrial.com", "Active User"),
	)
	monkeypatch.setattr(
		login_routes,
		"create_firebase_session_cookie",
		lambda uid_token: "firebase-session-cookie",
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
	db.add(
		User(
			firebase_uid="firebase-uid-111",
			email="refresh@jlptrial.com",
			name="Refresh User",
		)
	)
	db.commit()

	monkeypatch.setattr(
		"src.api.services.login.verify_firebase_session_cookie",
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


def test_firebase_logout_clears_session_cookie(client: TestClient, monkeypatch) -> None:
	called = {}

	def fake_revoke(uid: str) -> None:
		called["uid"] = uid

	monkeypatch.setattr(
		login_routes,
		"verify_firebase_session_cookie",
		lambda session_cookie: _firebase_identity("firebase-uid-222", "logout@jlptrial.com", "Logout User"),
	)
	monkeypatch.setattr(login_routes, "revoke_firebase_sessions", fake_revoke)

	client.cookies.set(SESSION_COOKIE_NAME, "firebase-session-cookie", path="/")
	response = client.post("/users/logout")
	client.cookies.clear()

	assert response.status_code == 200
	assert response.json() == {"message": "Logged out"}
	assert called["uid"] == "firebase-uid-222"
	assert SESSION_COOKIE_NAME in response.headers.get("set-cookie", "")
