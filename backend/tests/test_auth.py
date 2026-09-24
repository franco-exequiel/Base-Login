from fastapi.testclient import TestClient

from app.db import Base, engine
from app.main import app


def test_auth_flow() -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    client = TestClient(app)
    registered = client.post("/api/auth/register", json={"email": "test@example.com", "password": "secret123"})
    assert registered.status_code == 201
    login = client.post("/api/auth/login", data={"username": "test@example.com", "password": "secret123"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "test@example.com"
