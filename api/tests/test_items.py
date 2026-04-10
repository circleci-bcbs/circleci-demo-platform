"""Tests for /items CRUD endpoints."""

import json


def test_list_items_returns_200(client):
    resp = client.get("/items")
    assert resp.status_code == 200


def test_list_items_returns_seeded_data(client):
    data = client.get("/items").get_json()
    assert data["count"] >= 3


def test_list_items_filter_by_category(client):
    data = client.get("/items?category=hardware").get_json()
    assert all(item["category"] == "hardware" for item in data["items"])


def test_list_items_filter_empty_category(client):
    data = client.get("/items?category=nonexistent").get_json()
    assert data["count"] == 0


def test_get_item_by_id(client):
    resp = client.get("/items/1")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == "1"


def test_get_item_not_found(client):
    resp = client.get("/items/missing-id")
    assert resp.status_code == 404


def test_create_item_success(client):
    payload = {"name": "New Thing", "price": 9.99, "category": "misc"}
    resp = client.post("/items", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["name"] == "New Thing"
    assert data["price"] == 9.99


def test_create_item_default_category(client):
    payload = {"name": "No Category", "price": 1.00}
    resp = client.post("/items", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 201
    assert resp.get_json()["category"] == "general"


def test_create_item_appears_in_list(client):
    payload = {"name": "Listed Item", "price": 5.00}
    client.post("/items", data=json.dumps(payload), content_type="application/json")
    data = client.get("/items").get_json()
    names = [i["name"] for i in data["items"]]
    assert "Listed Item" in names
