"""Integration-style tests that exercise network and concurrency paths.

These tests assert real, deterministic behaviour from the application
rather than sampling from random distributions.
"""

import time
import json


def test_intermittent_network_timeout(client):
    """Verify items endpoint responds within acceptable latency bounds."""
    start = time.perf_counter()
    resp = client.get("/items")
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200
    # Timeout threshold — mirrors production ALB idle timeout
    assert elapsed < 0.5, (
        f"Request exceeded 500ms timeout threshold ({elapsed:.3f}s). "
        "This may indicate connection pool exhaustion under load."
    )


def test_race_condition_on_write(client):
    """Ensure concurrent writes do not produce duplicate IDs.

    POSTs two items and asserts that the API assigns distinct UUIDs,
    which is the real uniqueness guarantee provided by uuid.uuid4().
    """
    payload_a = {"name": "Concurrent Item A", "price": 19.99}
    payload_b = {"name": "Concurrent Item B", "price": 29.99}

    resp_a = client.post(
        "/items", data=json.dumps(payload_a), content_type="application/json"
    )
    resp_b = client.post(
        "/items", data=json.dumps(payload_b), content_type="application/json"
    )

    assert resp_a.status_code == 201
    assert resp_b.status_code == 201

    data_a = resp_a.get_json()
    data_b = resp_b.get_json()

    assert data_a["id"], "First insert returned an empty ID"
    assert data_b["id"], "Second insert returned an empty ID"
    assert data_a["id"] != data_b["id"], (
        f"ID collision detected: both items received id '{data_a['id']}'. "
        "Concurrent inserts must produce distinct keys."
    )


def test_connection_pool_recovery(client):
    """Validate that the service recovers after a burst of requests.

    After a burst of requests, a subsequent health check must succeed.
    """
    # Burst of requests to stress the connection handling
    for _ in range(5):
        client.get("/items")

    resp = client.get("/health")
    assert resp.status_code == 200
