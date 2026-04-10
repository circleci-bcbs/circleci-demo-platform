"""Tests for HTML template rendering and content structure."""


def test_home_has_valid_html_structure(client):
    resp = client.get("/")
    html = resp.data.decode()
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html


def test_home_has_viewport_meta(client):
    resp = client.get("/")
    assert b"viewport" in resp.data


def test_dashboard_has_valid_html_structure(client):
    resp = client.get("/dashboard")
    html = resp.data.decode()
    assert "<!DOCTYPE html>" in html
    assert "</html>" in html


def test_dashboard_shows_item_count(client):
    resp = client.get("/dashboard")
    html = resp.data.decode()
    # Should contain "Items (N)" header
    assert "Items (" in html


def test_dashboard_table_has_headers(client):
    resp = client.get("/dashboard")
    html = resp.data.decode()
    for header in ["ID", "Name", "Category", "Price"]:
        assert header in html


def test_dashboard_shows_api_status(client):
    resp = client.get("/dashboard")
    html = resp.data.decode()
    # Should show either Connected or Unreachable
    assert "Connected" in html or "Unreachable" in html


def test_dashboard_back_link(client):
    resp = client.get("/dashboard")
    assert b"Home" in resp.data
