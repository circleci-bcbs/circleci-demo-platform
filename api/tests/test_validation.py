"""Tests for input validation on item creation."""

import json


def test_create_item_missing_body(client):
    resp = client.post("/items", content_type="application/json")
    assert resp.status_code == 400


def test_create_item_missing_name(client):
    payload = {"price": 10.0}
    resp = client.post("/items", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 422
    assert "name" in resp.get_json()["details"][0].lower()


def test_create_item_empty_name(client):
    payload = {"name": "   ", "price": 10.0}
    resp = client.post("/items", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 422


def test_create_item_missing_price(client):
    payload = {"name": "No Price"}
    resp = client.post("/items", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 422
    assert "price" in resp.get_json()["details"][0].lower()


def test_create_item_negative_price(client):
    payload = {"name": "Negative", "price": -5}
    resp = client.post("/items", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 422


def test_create_item_invalid_price_type(client):
    payload = {"name": "Bad Price", "price": "not-a-number"}
    resp = client.post("/items", data=json.dumps(payload), content_type="application/json")
    assert resp.status_code == 422
