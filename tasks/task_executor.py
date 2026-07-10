"""Non-executing task executor contract for future work."""

from __future__ import annotations

import logging

from tasks.task import Task


class TaskExecutor:
    """Placeholder executor that intentionally does not run task work."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        """Initialize the executor placeholder."""
        self.initialized = True
        self._logger.info("task_executor_initialized")

    def can_execute(self, task: Task) -> bool:
        """Return whether a task could be executed in a future implementation."""
        return self.initialized and bool(task.name)

