"""Planning engine for executive reasoning."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from reasoning.decision_engine import DecisionResult, DecisionType


@dataclass(frozen=True, slots=True)
class ReasoningPlanModel:
    plan_type: str
    steps: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    required_systems: tuple[str, ...] = ()
    required_agents: tuple[str, ...] = ()
    required_providers: tuple[str, ...] = ()
    required_skills: tuple[str, ...] = ()
    required_plugins: tuple[str, ...] = ()
    execution_strategy: str = "direct"
    confidence: float = 0.0
    risk: float = 0.0
    complexity: str = "unknown"
    metadata: dict[str, object] = field(default_factory=dict)


class PlanningEngine:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("planning_engine_initialized")

    def generate(self, decision: DecisionResult) -> ReasoningPlanModel:
        self._ensure_initialized()
        if decision.best_action in {DecisionType.RESEARCH, DecisionType.CREATE_WORKFLOW}:
            plan_type = "research" if decision.best_action is DecisionType.RESEARCH else "project"
        elif decision.best_action in {DecisionType.CREATE_TASK, DecisionType.SCHEDULE}:
            plan_type = "sequential"
        elif decision.best_action is DecisionType.CLARIFY:
            plan_type = "simple"
        else:
            plan_type = "hybrid"
        return ReasoningPlanModel(
            plan_type=plan_type,
            steps=("understand", "reason", "evaluate", "select", "prepare_execution"),
            execution_strategy=decision.best_action.value,
            confidence=decision.confidence,
            risk=decision.risk,
            complexity=decision.complexity,
            metadata=dict(decision.metadata),
        )

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("PlanningEngine must be initialized before use.")
