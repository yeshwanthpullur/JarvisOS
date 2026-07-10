"""Task history store for completed task lifecycle records."""

from __future__ import annotations

import logging

from tasks.task import Task


class TaskHistory:
    """Stores terminal task records for future analytics."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._tasks: dict[str, Task] = {}
        self._logger = logger or logging.getLogger(__name__)

    def record(self, task: Task) -> None:
        """Record a terminal task state."""
        self._tasks[task.task_id] = task
        self._logger.info("task_history_recorded task_id=%s status=%s", task.task_id, task.status.value)

    def get(self, task_id: str) -> Task | None:
        """Return a historical task by ID."""
        return self._tasks.get(task_id)

    def list_tasks(self) -> tuple[Task, ...]:
        """Return all historical tasks."""
        return tuple(self._tasks.values())

    def count(self) -> int:
        """Return the number of historical task records."""
        return len(self._tasks)

