"""Background task processor with retry logic and exponential backoff."""

import sys
import os
import time
import logging
from dataclasses import dataclass, field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.config import get_config

config = get_config("worker")

logging.basicConfig(
    level=getattr(logging, config["log_level"]),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a unit of work to be processed."""

    id: str
    payload: dict
    status: str = "pending"
    retries: int = 0
    error: str | None = None


# ---------------------------------------------------------------------------
# Worker
# ---------------------------------------------------------------------------

class TaskWorker:
    """Processes tasks from an in-memory queue with retry and backoff."""

    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 0.1,
        backoff_factor: float = 2.0,
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_factor = backoff_factor
        self.queue: list[Task] = []
        self.completed: list[Task] = []
        self.failed: list[Task] = []

    # -- Queue management ---------------------------------------------------

    def enqueue(self, task: Task) -> None:
        """Add a task to the processing queue."""
        logger.info("Enqueued task %s", task.id)
        self.queue.append(task)

    def queue_size(self) -> int:
        return len(self.queue)

    # -- Processing ---------------------------------------------------------

    def process_task(self, task: Task, handler=None) -> Task:
        """Process a single task, retrying on failure up to *max_retries*.

        *handler* is a callable(task) -> dict.  If not supplied the default
        handler simply marks the task as completed.
        """
        handler = handler or self._default_handler

        while task.retries <= self.max_retries:
            try:
                handler(task)
                task.status = "completed"
                logger.info("Task %s completed", task.id)
                self.completed.append(task)
                return task
            except Exception as exc:
                task.retries += 1
                task.error = str(exc)
                delay = self._backoff_delay(task.retries)
                logger.warning(
                    "Task %s failed (attempt %d/%d): %s — retrying in %.2fs",
                    task.id,
                    task.retries,
                    self.max_retries + 1,
                    exc,
                    delay,
                )
                time.sleep(delay)

        task.status = "failed"
        logger.error("Task %s permanently failed after %d attempts", task.id, task.retries)
        self.failed.append(task)
        return task

    def process_all(self, handler=None) -> dict:
        """Drain the queue, processing every task.

        Returns a summary dict with counts of completed / failed tasks.
        """
        results = {"completed": 0, "failed": 0}
        while self.queue:
            task = self.queue.pop(0)
            result = self.process_task(task, handler)
            results[result.status] = results.get(result.status, 0) + 1
        return results

    # -- Helpers ------------------------------------------------------------

    def _backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay for the given attempt."""
        return self.base_delay * (self.backoff_factor ** (attempt - 1))

    @staticmethod
    def _default_handler(task: Task) -> dict:
        """No-op handler that always succeeds."""
        return {"processed": task.id}


# ---------------------------------------------------------------------------
# Entrypoint — run as a simple demo loop
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    worker = TaskWorker()

    # Seed some demo tasks.
    for i in range(5):
        worker.enqueue(Task(id=f"task-{i}", payload={"action": "process", "value": i}))

    summary = worker.process_all()
    logger.info("Processing complete: %s", summary)
# Worker service v0.1.1
# v0.1.2
