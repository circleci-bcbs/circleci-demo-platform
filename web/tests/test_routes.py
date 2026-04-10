"""Tests for web routes."""


def test_home_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_home_contains_title(client):
    resp = client.get("/")
    assert b"CircleCI Demo Platform" in resp.data


def test_home_contains_service_list(client):
    resp = client.get("/")
    assert b"API" in resp.data
    assert b"Worker" in resp.data
    assert b"Web" in resp.data


def test_home_contains_nav_links(client):
    resp = client.get("/")
    assert b"/dashboard" in resp.data
    assert b"/health" in resp.data


def test_health_returns_200(client):
    resp = client.get("/health")
    assert resp.status_code == 200


def test_health_status_ok(client):
    data = client.get("/health").get_json()
    assert data["status"] == "ok"
    assert data["service"] == "web"


def test_dashboard_returns_200(client):
    """Dashboard should render even when API is unreachable (mock fallback)."""
    resp = client.get("/dashboard")
    assert resp.status_code == 200


def test_dashboard_contains_items_table(client):
    resp = client.get("/dashboard")
    assert b"<table>" in resp.data


def test_dashboard_shows_fallback_items(client):
    """When API is down, mock items should appear."""
    resp = client.get("/dashboard")
    assert b"Widget A" in resp.data or b"widget" in resp.data.lower()
