"""Task scheduler architecture for future timed and parallel work."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ScheduledTask:
    """Scheduled task metadata without executing anything."""

    task_id: str
    run_at: datetime


class TaskScheduler:
    """Stores scheduled task metadata for future scheduling behavior."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._scheduled: dict[str, ScheduledTask] = {}
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        """Initialize the scheduler placeholder."""
        self.initialized = True
        self._logger.info("task_scheduler_initialized")

    def schedule(self, task_id: str, run_at: datetime) -> ScheduledTask:
        """Record a future scheduled task without executing it."""
        scheduled = ScheduledTask(task_id=task_id, run_at=run_at)
        self._scheduled[task_id] = scheduled
        self._logger.info("task_scheduled task_id=%s run_at=%s", task_id, run_at.isoformat())
        return scheduled

    def list_scheduled(self) -> tuple[ScheduledTask, ...]:
        """Return scheduled task metadata."""
        return tuple(self._scheduled.values())

