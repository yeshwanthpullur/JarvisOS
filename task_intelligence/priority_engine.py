"""Priority engine for task intelligence."""

from __future__ import annotations

import logging

from task_intelligence.models import TaskPriorityLevel


class PriorityEngine:
    """Compute priority metadata for work items."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("priority_engine_initialized")

    def determine_priority(self, importance: int = 0, deadline_urgent: bool = False) -> TaskPriorityLevel:
        self._ensure_initialized()
        if deadline_urgent or importance >= 90:
            return TaskPriorityLevel.CRITICAL
        if importance >= 70:
            return TaskPriorityLevel.HIGH
        if importance >= 30:
            return TaskPriorityLevel.NORMAL
        if importance > 0:
            return TaskPriorityLevel.LOW
        return TaskPriorityLevel.DEFERRED

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("PriorityEngine must be initialized before use.")
