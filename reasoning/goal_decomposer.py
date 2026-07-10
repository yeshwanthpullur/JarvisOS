"""Goal decomposition."""

from __future__ import annotations

import logging

from reasoning.reasoning_goal import ReasoningGoal


class GoalDecomposer:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("goal_decomposer_initialized")

    def decompose(self, goal: ReasoningGoal) -> dict[str, tuple[str, ...]]:
        self._ensure_initialized()
        return {
            "primary_goals": (goal.goal,),
            "secondary_goals": goal.assumptions,
            "sub_goals": (),
            "milestones": (),
            "tasks": (),
            "dependencies": goal.constraints,
            "required_knowledge": (),
            "required_memory": (),
            "required_research": (),
            "required_tools": (),
            "required_skills": (),
        }

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("GoalDecomposer must be initialized before use.")
