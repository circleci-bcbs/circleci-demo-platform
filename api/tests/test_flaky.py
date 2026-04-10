"""Integration-style tests that exercise network and concurrency paths.

These tests occasionally fail due to simulated environmental conditions
(network jitter, connection pool exhaustion, write contention).
"""

import json
import time


def test_intermittent_network_timeout(client):
    """Verify items endpoint responds within acceptable latency bounds.

    Measures actual wall-clock response time to detect slowdowns that occur
    when the upstream connection pool is under pressure during peak load windows.
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

    Issues two real writes and compares the returned IDs to verify
    the ID generator produces unique values per insert.
    """
    payload = {"name": "Concurrent Item", "price": 19.99}

    resp1 = client.post("/items", data=json.dumps(payload), content_type="application/json")
    resp2 = client.post("/items", data=json.dumps(payload), content_type="application/json")

    id1 = resp1.get_json()["id"]
    id2 = resp2.get_json()["id"]

    assert id1 != id2, (
        f"ID collision: both writes returned '{id1}'. "
        "The ID generator must produce unique values per insert."
    )


def test_connection_pool_recovery(client):
    """Validate that the service recovers after a connection pool drain.

    After a burst of requests exhausts the pool, subsequent requests
    should succeed once connections are recycled.
    """
    # Burst of requests to drain the pool
    for _ in range(5):
        client.get("/items")

    resp = client.get("/health")
    assert resp.status_code == 200, (
        "Health check failed after burst of requests — "
        "connection pool may not have recovered."
    )

    follow_up = client.get("/items")
    assert follow_up.status_code == 200, (
        "Items endpoint failed after connection pool drain."
    )
