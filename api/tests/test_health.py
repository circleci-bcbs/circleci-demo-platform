"""Tests for the /health endpoint."""


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_status_ok(client):
    data = client.get("/health").get_json()
    assert data["status"] == "ok"


def test_health_identifies_service(client):
    data = client.get("/health").get_json()
    assert data["service"] == "api"


def test_health_includes_uptime(client):
    data = client.get("/health").get_json()
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], (int, float))
