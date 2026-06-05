from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_register_login_me_flow():
    email = "pytest_user@test.com"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Pytest User",
            "email": email,
            "password": "password123",
            "role": "user"
        }
    )

    assert register_response.status_code in [200, 400]

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert me_response.status_code == 200

    data = me_response.json()

    assert data["email"] == email
    