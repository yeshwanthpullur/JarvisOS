"""Milestone management layer for task intelligence."""

from __future__ import annotations

import logging

from task_intelligence.models import MilestoneRecord


class MilestoneManager:
    """Create and track milestones."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._milestones: dict[str, MilestoneRecord] = {}
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("milestone_manager_initialized")

    def create_milestone(
        self,
        name: str,
        description: str = "",
        project_id: str | None = None,
        goal_id: str | None = None,
    ) -> MilestoneRecord:
        self._ensure_initialized()
        milestone = MilestoneRecord(name=name, description=description, project_id=project_id, goal_id=goal_id)
        self._milestones[milestone.milestone_id] = milestone
        self._logger.info("milestone_created milestone_id=%s", milestone.milestone_id)
        return milestone

    def statistics(self) -> dict[str, object]:
        self._ensure_initialized()
        return {"milestones": len(self._milestones), "status": "ready"}

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("MilestoneManager must be initialized before use.")
