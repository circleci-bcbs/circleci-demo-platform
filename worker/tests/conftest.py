"""Shared fixtures for worker tests."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from worker.worker import TaskWorker, Task


@pytest.fixture
def worker():
    """Return a fresh TaskWorker with fast retry settings for tests."""
    return TaskWorker(max_retries=3, base_delay=0.001, backoff_factor=1.0)


@pytest.fixture
def sample_task():
    """Return a single sample task."""
    return Task(id="test-1", payload={"action": "test"})
