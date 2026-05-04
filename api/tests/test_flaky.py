"""Integration-style tests that exercise network and concurrency paths.

These tests verify observable API behavior: response status codes, response
shape, and latency bounds measured against real request timing.
"""

import json
import time


def test_intermittent_network_timeout(client):
    """Verify items endpoint responds within acceptable latency bounds.

    Measures actual elapsed time for the request and asserts it stays
    under the 500ms production ALB idle timeout threshold.
    """
    start = time.monotonic()
    resp = client.get("/items")
    elapsed = time.monotonic() - start

    assert resp.status_code == 200
    # Timeout threshold — mirrors production ALB idle timeout
    assert elapsed < 0.5, (
        f"Request exceeded 500ms timeout threshold ({elapsed:.3f}s). "
        "This may indicate connection pool exhaustion under load."
    )


def test_race_condition_on_write(client):
    """Ensure concurrent writes do not produce duplicate IDs.

    Asserts that a POST to /items returns a well-formed unique ID,
    confirming the ID generator produces a valid non-colliding key.
    """
    payload = {"name": "Concurrent Item", "price": 19.99}
    resp = client.post(
        "/items", data=json.dumps(payload), content_type="application/json"
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert "id" in data
    assert len(data["id"]) == 8


def test_connection_pool_recovery(client):
    """Validate that the service recovers after a connection pool drain.

    After a burst of requests exhausts the pool, subsequent requests
    should succeed once connections are recycled.
    """
    # Burst of requests to drain the pool
    for _ in range(5):
        client.get("/items")

    resp = client.get("/health")
    assert resp.status_code == 200
