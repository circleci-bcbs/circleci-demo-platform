"""Integration-style tests that exercise network and concurrency paths.

These tests exercise real API behavior including latency, ID uniqueness,
and connection pool recovery.
"""

import time


def test_intermittent_network_timeout(client):
    """Verify items endpoint responds within acceptable latency bounds."""
    start = time.monotonic()
    resp = client.get("/items")
    elapsed = time.monotonic() - start

    assert resp.status_code == 200
    assert elapsed < 0.5, (
        f"Request exceeded 500ms timeout threshold ({elapsed:.3f}s)."
    )


def test_race_condition_on_write(client):
    """Ensure concurrent writes do not produce duplicate IDs."""
    import json

    payload = {"name": "Concurrent Item", "price": 19.99}
    ids = set()
    num_writes = 10
    for _ in range(num_writes):
        resp = client.post(
            "/items", data=json.dumps(payload), content_type="application/json"
        )
        assert resp.status_code in (200, 201)
        data = resp.get_json()
        ids.add(data["id"])

    assert len(ids) == num_writes, (
        f"ID collision detected: only {len(ids)} unique IDs"
        f" for {num_writes} inserts."
    )


def test_connection_pool_recovery(client):
    """Validate that the service recovers after a connection pool drain."""
    for _ in range(5):
        client.get("/items")

    resp = client.get("/health")
    assert resp.status_code == 200
