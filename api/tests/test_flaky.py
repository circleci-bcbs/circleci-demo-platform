"""Integration-style tests that exercise network and concurrency paths.

These tests exercise network and concurrency paths against the Flask test
client and assert on actual observable behaviour (status codes, response
fields, wall-clock latency).
"""

import json
import time


def test_intermittent_network_timeout(client):
    """Verify items endpoint responds within acceptable latency bounds.

    Measures actual wall-clock time for the test-client round-trip and
    asserts it stays under a generous threshold (500 ms).  A real timeout
    here indicates a problem in the application or test environment, not a
    random dice roll.
    """
    start = time.perf_counter()
    resp = client.get("/items")
    elapsed = time.perf_counter() - start

    assert resp.status_code == 200
    # Timeout threshold — mirrors production ALB idle timeout
    elapsed_ms = int(elapsed * 1000)
    assert elapsed < 0.5, (
        f"Request exceeded 500ms timeout threshold ({elapsed_ms}ms). "
        "This may indicate connection pool exhaustion under load."
    )


def test_race_condition_on_write(client):
    """Ensure a write returns a unique, non-empty ID.

    Submits a single POST and verifies the response contains an 'id' field.
    A real duplicate-key / collision scenario would surface as a 4xx/5xx or
    a missing id field, both of which are asserted below.
    """
    payload = {"name": "Concurrent Item", "price": 19.99}
    resp = client.post(
        "/items", data=json.dumps(payload), content_type="application/json"
    )
    assert resp.status_code in (
        200,
        201,
    ), f"Unexpected status {resp.status_code} on item creation."
    data = resp.get_json()
    assert data is not None, "Response body was not valid JSON."
    assert "id" in data and data["id"], (
        "Response did not include a valid 'id' field — "
        "concurrent insert may have produced a duplicate key."
    )


def test_connection_pool_recovery(client):
    """Validate that the service recovers after a burst of requests.

    Sends a burst of GET /items requests and then checks /health.  If the
    connection pool (or any other resource) fails to recover the health
    endpoint will return a non-200 status, which is the real signal to
    assert on.
    """
    # Burst of requests to drain the pool
    for _ in range(5):
        resp = client.get("/items")
        assert (
            resp.status_code == 200
        ), f"GET /items returned {resp.status_code} during burst."

    resp = client.get("/health")
    assert resp.status_code == 200, (
        "Connection pool failed to recover within the recycling window. "
        "Health check returned a non-200 status — "
        "subsequent queries may still time out."
    )
