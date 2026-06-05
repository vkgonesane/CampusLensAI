import time

from fastapi.testclient import TestClient

from app.main import app
from app.services import signal_service

client = TestClient(app)


def _register_and_login_user():
    unique = int(time.time() * 1000)
    email = f"signal_user_{unique}@test.com"

    register_response = client.post(
        "/auth/register",
        json={
            "full_name": "Signal Test User",
            "email": email,
            "password": "password123",
            "role": "user",
        },
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "password123",
        },
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def test_user_can_create_signal_with_ai_and_sla_fields(monkeypatch):
    def fake_analyze_signal(*args, **kwargs):
        return {
            "ai_category": "water",
            "ai_sentiment": "negative",
            "ai_priority": "high",
            "ai_summary": "Mocked AI summary",
            "suggested_department": "Plumbing Department",
            "duplicate_score": 0.0,
            "hotspot_score": 0.1,
        }

    monkeypatch.setattr(signal_service, "analyze_signal", fake_analyze_signal)

    token = _register_and_login_user()

    response = client.post(
        "/signals/",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "title": "Water leakage near hostel",
            "description": "Water is leaking continuously from a broken pipe near hostel entrance.",
            "category": "Maintenance",
            "location_name": "Hostel Block A",
            "latitude": 28.6139,
            "longitude": 77.209,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Water leakage near hostel"
    assert data["status"] == "submitted"
    assert data["created_by"] is not None

    assert data["ai_category"] == "water"
    assert data["ai_sentiment"] == "negative"
    assert data["ai_priority"] == "high"
    assert data["ai_summary"] == "Mocked AI summary"
    assert data["suggested_department"] == "Plumbing Department"

    assert data["duplicate_score"] == 0.0
    assert data["hotspot_score"] == 0.1

    assert data["sla_due_at"] is not None
    assert data["sla_breached"] is False
    assert data["escalated_at"] is None