"""Executive reasoning engine."""

from __future__ import annotations

import logging

from reasoning.confidence_engine import ConfidenceEngine
from reasoning.decision_engine import DecisionEngine, DecisionResult
from reasoning.goal_decomposer import GoalDecomposer
from reasoning.option_generator import OptionGenerator
from reasoning.planning_engine import PlanningEngine, ReasoningPlanModel
from reasoning.reasoning_context import ReasoningContext
from reasoning.reasoning_request import ReasoningRequest
from reasoning.reasoning_response import ReasoningResponse
from reasoning.reasoning_validator import ReasoningValidator


class ReasoningEngine:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.decision_engine = DecisionEngine(logger=self._logger)
        self.planning_engine = PlanningEngine(logger=self._logger)
        self.goal_decomposer = GoalDecomposer(logger=self._logger)
        self.option_generator = OptionGenerator(logger=self._logger)
        self.evaluation_engine = self.decision_engine.evaluation_engine
        self.confidence_engine = ConfidenceEngine(logger=self._logger)
        self.validator = ReasoningValidator(logger=self._logger)
        self.initialized = False

    def initialize(self) -> None:
        self.decision_engine.initialize()
        self.planning_engine.initialize()
        self.goal_decomposer.initialize()
        self.option_generator.initialize()
        self.confidence_engine.initialize()
        self.validator.initialize()
        self.initialized = True
        self._logger.info("reasoning_engine_initialized")

    def reason(self, request: ReasoningRequest, context: ReasoningContext | None = None) -> ReasoningResponse:
        self._ensure_initialized()
        if not self.validator.validate_request(request):
            raise ValueError("Reasoning request is invalid.")
        normalized = request.content.strip()
        intent = self._infer_intent(normalized)
        missing_information = self._infer_missing_information(normalized)
        objective = self._infer_goal(normalized)
        reasoning_metadata = {
            "confidence": self._confidence(normalized),
            "risk": 0.2 if missing_information else 0.05,
            "cost": 0.0,
            "complexity": "complex" if len(normalized) > 80 else "moderate",
        }
        decision = self.decision_engine.evaluate(objective, reasoning_metadata)
        plan = self.planning_engine.generate(decision)
        confidence_label = self.confidence_engine.determine(
            decision=decision.confidence,
            knowledge=0.7,
            memory=0.7,
            research=0.6,
            execution=0.6,
        )
        response = ReasoningResponse(
            goal=objective,
            intent=intent,
            missing_information=missing_information,
            alternatives=self.option_generator.generate(objective),
            plans=(plan.plan_type, *plan.steps),
            recommended_action=decision.best_action,
            confidence=decision.confidence,
            risk=decision.risk,
            cost=decision.cost,
            complexity=decision.complexity,
            metadata={
                "decision": decision,
                "plan": plan,
                "confidence_label": confidence_label,
                "context": context.context if context else {},
            },
        )
        self._logger.info("reasoning_completed request_id=%s action=%s", request.request_id, response.recommended_action.value)
        return response

    def _infer_intent(self, content: str) -> str:
        lowered = content.lower()
        if "research" in lowered:
            return "research"
        if "plan" in lowered:
            return "planning"
        if "task" in lowered:
            return "task"
        if "workflow" in lowered:
            return "workflow"
        if "clarify" in lowered:
            return "clarify"
        return "conversation"

    def _infer_goal(self, content: str) -> str:
        return content or "Handle empty request"

    def _infer_missing_information(self, content: str) -> tuple[str, ...]:
        return ("context",) if "?" in content or len(content.split()) < 3 else ()

    def _confidence(self, content: str) -> float:
        return 0.9 if len(content.split()) > 3 else 0.5

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReasoningEngine must be initialized before use.")
