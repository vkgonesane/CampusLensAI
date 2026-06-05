from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_missing_fields():
    response = client.post(
        "/auth/register",
        json={}
    )

    assert response.status_code == 422


def test_login_missing_fields():
    response = client.post(
        "/auth/login",
        data={}
    )

    assert response.status_code in [400, 422]