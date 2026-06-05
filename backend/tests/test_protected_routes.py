from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_signals_requires_auth():
    response = client.get("/signals")

    assert response.status_code in [401, 403]


def test_notifications_requires_auth():
    response = client.get("/notifications")

    assert response.status_code in [401, 403]


def test_users_requires_auth():
    response = client.get("/users")

    assert response.status_code in [401, 403]