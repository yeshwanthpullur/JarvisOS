"""Dashboard for task intelligence."""

from __future__ import annotations

import logging


class TaskDashboard:
    """Render summaries for projects, goals, and milestones."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("task_dashboard_initialized")

    def summary(self) -> dict[str, object]:
        self._ensure_initialized()
        return {"status": "ready"}

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("TaskDashboard must be initialized before use.")
