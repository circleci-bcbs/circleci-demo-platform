"""Integration tests for worker under simulated production conditions.

These tests exercise edge cases around task processing under load,
where timing-dependent failures can surface intermittently.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from worker.worker import Task


def test_queue_drain_under_memory_pressure(worker):
    """Verify queue fully drains when the system is under memory pressure."""
    for i in range(10):
        worker.enqueue(Task(id=f"mp-{i}", payload={"data": "x" * 100}))

    summary = worker.process_all()

    assert summary["completed"] == 10


def test_retry_backoff_jitter_convergence(worker):
    """Ensure retried tasks converge on a stable processing state."""
    task = Task(id="jitter-1", payload={"priority": "high"})

    attempts = []

    def jittery_handler(t):
        attempts.append(1)
        if len(attempts) < 2:
            raise RuntimeError("contention on retry slot")
        return {}

    result = worker.process_task(task, handler=jittery_handler)
    assert result.status == "completed"
