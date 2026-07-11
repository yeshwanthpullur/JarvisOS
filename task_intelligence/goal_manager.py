"""Goal management layer for task intelligence."""

from __future__ import annotations

import logging
from datetime import timedelta

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
        *,
        purpose: str = "",
        desired_outcome: str = "",
        success_criteria: tuple[str, ...] = (),
        parent_goal_id: str | None = None,
        priority: TaskPriorityLevel = TaskPriorityLevel.NORMAL,
        target_date: str | None = None,
        time_horizon: str = "open_ended",
        source: str = "task_intelligence",
        audit_metadata: dict[str, object] | None = None,
    ) -> GoalRecord:
        self._ensure_initialized()
        goal = GoalRecord(
            name=name,
            description=description,
            project_id=project_id,
            parent_goal_id=parent_goal_id,
            purpose=purpose,
            desired_outcome=desired_outcome,
            success_criteria=success_criteria,
            priority=priority,
            target_date=target_date,
            time_horizon=time_horizon,
            source=source,
            audit_metadata=dict(audit_metadata or {}),
            start_date=utc_now().isoformat(),
        )
        self._goals[goal.goal_id] = goal
        self._logger.info("goal_created goal_id=%s", goal.goal_id)
        return goal

    def update_goal(self, goal_id: str, **changes: object) -> GoalRecord | None:
        self._ensure_initialized()
        goal = self._goals.get(goal_id)
        if goal is None:
            return None
        for field_name, value in changes.items():
            if hasattr(goal, field_name):
                setattr(goal, field_name, value)
        goal.updated_at = utc_now()
        goal.history = (*goal.history, f"Updated fields: {', '.join(sorted(changes))}")
        self._logger.info("goal_updated goal_id=%s fields=%s", goal_id, ",".join(sorted(changes)))
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

    def get_goal(self, goal_id: str) -> GoalRecord | None:
        self._ensure_initialized()
        return self._goals.get(goal_id)

    def list_goals(self) -> tuple[GoalRecord, ...]:
        self._ensure_initialized()
        return tuple(self._goals.values())

    def search_goals(self, query: str) -> tuple[GoalRecord, ...]:
        self._ensure_initialized()
        normalized = query.strip().lower()
        results = tuple(
            goal
            for goal in self._goals.values()
            if normalized in goal.name.lower()
            or normalized in goal.description.lower()
            or normalized in goal.purpose.lower()
            or normalized in goal.desired_outcome.lower()
            or normalized in goal.goal_id.lower()
        )
        self._logger.info("goal_search query=%s count=%s", query, len(results))
        return results

    def set_status(self, goal_id: str, status: str) -> GoalRecord | None:
        self._ensure_initialized()
        goal = self._goals.get(goal_id)
        if goal is None:
            return None
        goal.status = status
        if status == "active" and goal.start_date is None:
            goal.start_date = utc_now().isoformat()
        if status == "completed" and goal.completion_date is None:
            goal.completion_date = utc_now().isoformat()
            goal.progress = 1.0
        goal.updated_at = utc_now()
        goal.history = (*goal.history, f"Status changed to {status}")
        self._logger.info("goal_status_changed goal_id=%s status=%s", goal_id, status)
        return goal

    def pause_goal(self, goal_id: str) -> GoalRecord | None:
        return self.set_status(goal_id, "paused")

    def resume_goal(self, goal_id: str) -> GoalRecord | None:
        return self.set_status(goal_id, "active")

    def abandon_goal(self, goal_id: str, reason: str = "") -> GoalRecord | None:
        goal = self.set_status(goal_id, "abandoned")
        if goal is not None and reason:
            goal.audit_metadata["abandon_reason"] = reason
        return goal

    def supersede_goal(self, goal_id: str, successor_goal_id: str, reason: str = "") -> GoalRecord | None:
        goal = self._goals.get(goal_id)
        successor = self._goals.get(successor_goal_id)
        if goal is None or successor is None:
            return None
        goal.status = "superseded"
        goal.related_goal_references = tuple({*goal.related_goal_references, successor_goal_id})
        goal.audit_metadata["superseded_by"] = successor_goal_id
        if reason:
            goal.audit_metadata["supersede_reason"] = reason
        goal.updated_at = utc_now()
        self._logger.info("goal_superseded goal_id=%s successor=%s", goal_id, successor_goal_id)
        return goal

    def link_task(self, goal_id: str, task_id: str) -> GoalRecord | None:
        self._ensure_initialized()
        goal = self._goals.get(goal_id)
        if goal is None:
            return None
        goal.task_references = tuple(dict.fromkeys((*goal.task_references, task_id)))
        goal.updated_at = utc_now()
        self._logger.info("goal_task_linked goal_id=%s task_id=%s", goal_id, task_id)
        return goal

    def link_milestone(self, goal_id: str, milestone_id: str) -> GoalRecord | None:
        self._ensure_initialized()
        goal = self._goals.get(goal_id)
        if goal is None:
            return None
        goal.milestones = tuple(dict.fromkeys((*goal.milestones, milestone_id)))
        goal.updated_at = utc_now()
        self._logger.info("goal_milestone_linked goal_id=%s milestone_id=%s", goal_id, milestone_id)
        return goal

    def review_goal(self, goal_id: str, summary: str = "", next_review_days: int = 7) -> GoalRecord | None:
        self._ensure_initialized()
        goal = self._goals.get(goal_id)
        if goal is None:
            return None
        goal.last_reviewed = utc_now()
        goal.next_review = goal.last_reviewed + timedelta(days=max(1, next_review_days))
        goal.audit_metadata["review_summary"] = summary
        goal.updated_at = utc_now()
        self._logger.info("goal_reviewed goal_id=%s", goal_id)
        return goal

    def statistics(self) -> dict[str, object]:
        self._ensure_initialized()
        return {"goals": len(self._goals), "status": "ready"}

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("GoalManager must be initialized before use.")
