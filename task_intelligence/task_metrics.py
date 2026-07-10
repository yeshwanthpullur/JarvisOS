"""Task intelligence metrics."""

from __future__ import annotations

import logging
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskMetricsSnapshot:
    projects: int
    goals: int
    milestones: int
    tasks: int


class TaskMetrics:
    """Metrics placeholder for task intelligence."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("task_metrics_initialized")

    def snapshot(self) -> TaskMetricsSnapshot:
        self._ensure_initialized()
        return TaskMetricsSnapshot(0, 0, 0, 0)

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("TaskMetrics must be initialized before use.")
