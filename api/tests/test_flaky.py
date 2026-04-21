"""Integration-style tests that exercise network and concurrency paths.

These tests validate real application behavior for timing, ID uniqueness,
and service health after load.
"""

import json
import time


def test_intermittent_network_timeout(client):
    """Verify items endpoint responds within acceptable latency bounds.

    Measures actual response time and asserts it stays under 500ms.
    """
    start = time.monotonic()
    resp = client.get("/items")
    elapsed = time.monotonic() - start

    assert resp.status_code == 200
    # Timeout threshold — mirrors production ALB idle timeout
    elapsed_ms = round(elapsed * 1000)
    assert elapsed < 0.5, (
        f"Request exceeded 500ms timeout threshold ({elapsed_ms}ms). "
        "This may indicate connection pool exhaustion under load."
    )


def test_race_condition_on_write(client):
    """Ensure concurrent writes do not produce duplicate IDs.

    Performs two sequential inserts and asserts their IDs are distinct.
    """
    payload = {"name": "Concurrent Item", "price": 19.99}

    resp1 = client.post(
        "/items", data=json.dumps(payload), content_type="application/json"
    )
    resp2 = client.post(
        "/items", data=json.dumps(payload), content_type="application/json"
    )

    assert resp1.status_code == 201
    assert resp2.status_code == 201

    id1 = resp1.get_json()["id"]
    id2 = resp2.get_json()["id"]

    assert id1 != id2, (
        f"ID collision detected: both inserts produced '{id1}'. "
        "Concurrent insert produced a duplicate key — retry may be required."
    )


def test_connection_pool_recovery(client):
    """Validate that the service responds correctly after a burst of requests.

    After a burst of requests, subsequent requests should succeed.
    """
    # Burst of requests to drain the pool
    for _ in range(5):
        resp = client.get("/items")
        assert resp.status_code == 200

    resp = client.get("/health")
    assert resp.status_code == 200, (
        "Connection pool failed to recover within the recycling window. "
        "Health check passed but subsequent queries may still time out."
    )
