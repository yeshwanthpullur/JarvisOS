"""Decision engine for executive reasoning."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import StrEnum

from reasoning.evaluation_engine import EvaluationEngine
from reasoning.option_generator import OptionGenerator


class DecisionType(StrEnum):
    ANSWER = "answer"
    CLARIFY = "clarify"
    RETRIEVE = "retrieve"
    RESEARCH = "research"
    PLAN = "plan"
    EXECUTE = "execute"
    DELEGATE = "delegate"
    SCHEDULE = "schedule"
    CREATE_WORKFLOW = "create_workflow"
    CREATE_TASK = "create_task"
    REJECT = "reject"
    ESCALATE = "escalate"


@dataclass(frozen=True, slots=True)
class DecisionResult:
    best_action: DecisionType
    ranked_options: tuple[str, ...] = ()
    confidence: float = 0.0
    risk: float = 0.0
    cost: float = 0.0
    complexity: str = "unknown"
    metadata: dict[str, object] = field(default_factory=dict)


class DecisionEngine:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.option_generator = OptionGenerator(logger=self._logger)
        self.evaluation_engine = EvaluationEngine(logger=self._logger)
        self.initialized = False

    def initialize(self) -> None:
        self.option_generator.initialize()
        self.evaluation_engine.initialize()
        self.initialized = True
        self._logger.info("decision_engine_initialized")

    def evaluate(self, objective: str, reasoning_metadata: dict[str, object]) -> DecisionResult:
        self._ensure_initialized()
        options = self.option_generator.generate(objective)
        scores = self.evaluation_engine.evaluate(options)
        ranked = tuple(sorted(options, key=lambda option: scores[option], reverse=True))
        best = ranked[0] if ranked else "best"
        if "clarify" in objective.lower():
            action = DecisionType.CLARIFY
        elif "research" in objective.lower():
            action = DecisionType.RESEARCH
        elif "task" in objective.lower():
            action = DecisionType.CREATE_TASK
        elif "workflow" in objective.lower():
            action = DecisionType.CREATE_WORKFLOW
        elif "plan" in objective.lower():
            action = DecisionType.PLAN
        else:
            action = DecisionType.ANSWER
        return DecisionResult(
            best_action=action,
            ranked_options=ranked,
            confidence=float(reasoning_metadata.get("confidence", 0.5)),
            risk=float(reasoning_metadata.get("risk", 0.2)),
            cost=float(reasoning_metadata.get("cost", 0.0)),
            complexity=str(reasoning_metadata.get("complexity", "unknown")),
            metadata={"best_option": best, **reasoning_metadata},
        )

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("DecisionEngine must be initialized before use.")
