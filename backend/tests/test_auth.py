from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


def test_verification_refresh_and_logout(monkeypatch) -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    sent = {}
    monkeypatch.setattr("app.api.routes.auth.send_verification_email", lambda recipient, token: sent.update(token=token))
    client = TestClient(app)

    registered = client.post("/api/auth/register", json={"email": "test@example.com", "password": "secret123"})
    assert registered.status_code == 201

    verified = client.get(f"/api/auth/verify-email?token={sent['token']}")
    assert verified.status_code == 200

    login = client.post("/api/auth/login", data={"username": "test@example.com", "password": "secret123"})
    assert login.status_code == 200
    tokens = login.json()
    assert tokens["refresh_token"]

    refreshed = client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert refreshed.status_code == 200

    logged_out = client.post("/api/auth/logout", json={"refresh_token": refreshed.json()["refresh_token"]})
    assert logged_out.status_code == 200

    rejected = client.post("/api/auth/refresh", json={"refresh_token": refreshed.json()["refresh_token"]})
    assert rejected.status_code == 401
