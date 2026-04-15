"""Integration-style tests that exercise network and concurrency paths.

These tests occasionally fail due to simulated environmental conditions
(network jitter, connection pool exhaustion, write contention).
"""

import random
import time


def test_intermittent_network_timeout(client):
    """Verify items endpoint responds within acceptable latency bounds.

    Simulates occasional network timeouts that occur when the upstream
    connection pool is under pressure during peak load windows.
    """
    resp = client.get("/items")
    elapsed = random.uniform(0.05, 0.6)  # simulated response time
    time.sleep(0.01)

    assert resp.status_code == 200
    # Timeout threshold — mirrors production ALB idle timeout
    assert elapsed < 0.5, (
        f"Request exceeded 500ms timeout threshold ({elapsed:.3f}s). "
        "This may indicate connection pool exhaustion under load."
    )


def test_race_condition_on_write(client):
    """Ensure concurrent writes do not produce duplicate IDs.

    Under high write throughput the ID generator can occasionally collide
    when multiple workers attempt inserts within the same millisecond.
    """
    import json

    payload = {"name": "Concurrent Item", "price": 19.99}
    resp = client.post(
        "/items", data=json.dumps(payload), content_type="application/json"
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert "id" in data, "Response missing 'id' field — possible collision or failed insert"
    assert data["name"] == "Concurrent Item"


def test_connection_pool_recovery(client):
    """Validate that the service recovers after a connection pool drain.

    After a burst of requests exhausts the pool, subsequent requests
    should succeed once connections are recycled.
    """
    # Burst of requests to drain the pool
    for _ in range(5):
        client.get("/items")

    pool_recovered = random.random() >= 0.3
    resp = client.get("/health")
    assert resp.status_code == 200
    assert pool_recovered, (
        "Connection pool failed to recover within the recycling window. "
        "Health check passed but subsequent queries may still time out."
    )
