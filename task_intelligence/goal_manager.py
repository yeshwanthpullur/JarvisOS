"""Goal management layer for task intelligence."""

from __future__ import annotations

import logging

from task_intelligence.models import GoalRecord, TaskPriorityLevel, utc_now


class GoalManager:
    """Create and track goals for projects."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._goals: dict[str, GoalRecord] = {}
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("goal_manager_initialized")

    def create_goal(
        self,
        name: str,
        description: str = "",
        project_id: str | None = None,
        priority: TaskPriorityLevel = TaskPriorityLevel.NORMAL,
    ) -> GoalRecord:
        self._ensure_initialized()
        goal = GoalRecord(name=name, description=description, project_id=project_id, priority=priority)
        self._goals[goal.goal_id] = goal
        self._logger.info("goal_created goal_id=%s", goal.goal_id)
        return goal

    def update_progress(self, goal_id: str, progress: float) -> GoalRecord | None:
        self._ensure_initialized()
        goal = self._goals.get(goal_id)
        if goal is None:
            return None
        goal.progress = max(0.0, min(1.0, progress))
        goal.updated_at = utc_now()
        self._logger.info("goal_progress_updated goal_id=%s progress=%s", goal_id, goal.progress)
        return goal

    def statistics(self) -> dict[str, object]:
        self._ensure_initialized()
        return {"goals": len(self._goals), "status": "ready"}

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("GoalManager must be initialized before use.")
