from fastapi.testclient import TestClient

from app.app import create_app

client = TestClient(create_app())


def test_health_returns_200():
    response = client.get("/api/v1/health")
    assert response.status_code == 200


def test_health_returns_ok_status():
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_returns_service_name():
    response = client.get("/api/v1/health")
    data = response.json()
    assert data["service"] == "ai-engine"
