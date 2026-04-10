"""Core worker functionality tests."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from worker.worker import Task


def test_enqueue_increases_queue_size(worker):
    task = Task(id="q-1", payload={})
    worker.enqueue(task)
    assert worker.queue_size() == 1


def test_enqueue_multiple_tasks(worker):
    for i in range(5):
        worker.enqueue(Task(id=f"q-{i}", payload={}))
    assert worker.queue_size() == 5


def test_process_task_succeeds(worker, sample_task):
    result = worker.process_task(sample_task)
    assert result.status == "completed"


def test_process_task_records_in_completed(worker, sample_task):
    worker.process_task(sample_task)
    assert len(worker.completed) == 1


def test_process_all_drains_queue(worker):
    for i in range(3):
        worker.enqueue(Task(id=f"drain-{i}", payload={}))
    worker.process_all()
    assert worker.queue_size() == 0


def test_process_all_returns_summary(worker):
    for i in range(3):
        worker.enqueue(Task(id=f"sum-{i}", payload={}))
    summary = worker.process_all()
    assert summary["completed"] == 3
    assert summary["failed"] == 0


def test_task_initial_status():
    task = Task(id="init", payload={"x": 1})
    assert task.status == "pending"
    assert task.retries == 0


def test_custom_handler(worker, sample_task):
    called = []

    def handler(task):
        called.append(task.id)
        return {}

    worker.process_task(sample_task, handler=handler)
    assert called == ["test-1"]
