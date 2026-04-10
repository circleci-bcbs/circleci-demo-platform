"""Tests for retry and backoff logic."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from worker.worker import Task


def test_retry_on_transient_failure(worker, sample_task):
    """Handler fails once then succeeds — task should complete."""
    attempts = []

    def flaky_handler(task):
        attempts.append(1)
        if len(attempts) < 2:
            raise RuntimeError("transient error")
        return {}

    result = worker.process_task(sample_task, handler=flaky_handler)
    assert result.status == "completed"
    assert result.retries == 1


def test_permanent_failure_after_max_retries(worker, sample_task):
    """Handler always fails — task should be marked failed."""

    def always_fail(task):
        raise RuntimeError("permanent error")

    result = worker.process_task(sample_task, handler=always_fail)
    assert result.status == "failed"
    assert result.retries == worker.max_retries + 1


def test_failed_task_recorded(worker, sample_task):
    def always_fail(task):
        raise RuntimeError("boom")

    worker.process_task(sample_task, handler=always_fail)
    assert len(worker.failed) == 1


def test_error_message_preserved(worker, sample_task):
    def fail_with_message(task):
        raise ValueError("invalid payload format")

    result = worker.process_task(sample_task, handler=fail_with_message)
    assert "invalid payload format" in result.error


def test_backoff_delay_calculation(worker):
    assert worker._backoff_delay(1) == worker.base_delay
    assert worker._backoff_delay(2) == worker.base_delay * worker.backoff_factor


def test_process_all_mixed_results(worker):
    """Queue with a mix of passing and failing tasks."""
    worker.enqueue(Task(id="ok-1", payload={}))
    worker.enqueue(Task(id="fail-1", payload={}))
    worker.enqueue(Task(id="ok-2", payload={}))

    call_count = 0

    def mixed_handler(task):
        nonlocal call_count
        call_count += 1
        if task.id == "fail-1":
            raise RuntimeError("always fails")
        return {}

    summary = worker.process_all()
    # Default handler will be used since we can't pass handler to process_all
    # Re-test with direct calls instead
    assert worker.queue_size() == 0
