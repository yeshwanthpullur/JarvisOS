"""Manager for executive reasoning."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from reasoning.reasoning_context import ReasoningContext
from reasoning.reasoning_diagnostics import ReasoningDiagnostics
from reasoning.reasoning_engine import ReasoningEngine
from reasoning.reasoning_history import ReasoningHistory, ReasoningHistoryRecord
from reasoning.reasoning_logger import ReasoningLogger
from reasoning.reasoning_metrics import ReasoningMetrics
from reasoning.reasoning_request import ReasoningRequest
from reasoning.reasoning_response import ReasoningResponse
from reasoning.reasoning_validator import ReasoningValidator


@dataclass(frozen=True, slots=True)
class ReasoningStatistics:
    reasoning_status: str
    decision_status: str
    planning_status: str
    confidence_status: str
    overall_intelligence_status: str


class ReasoningManager:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.engine = ReasoningEngine(logger=self.logger)
        self.history = ReasoningHistory(logger=self.logger)
        self.metrics = ReasoningMetrics()
        self.diagnostics = ReasoningDiagnostics()
        self.reasoning_logger = ReasoningLogger(logger=self.logger)
        self.validator = ReasoningValidator(logger=self.logger)
        self.initialized = False

    def initialize(self) -> ReasoningStatistics:
        self.engine.initialize()
        self.history.initialize()
        self.metrics.initialize()
        self.diagnostics.initialize()
        self.validator.initialize()
        self.initialized = True
        self.logger.info("reasoning_manager_initialized")
        return self.statistics()

    def reason(self, request: ReasoningRequest, context: ReasoningContext | None = None) -> ReasoningResponse:
        self._ensure_initialized()
        response = self.engine.reason(request, context)
        self.metrics.requests += 1
        self.metrics.decisions += 1
        self.metrics.plans += 1
        decision = response.metadata.get("decision")
        plan = response.metadata.get("plan")
        self.history.record(
            ReasoningHistoryRecord(
                request_id=request.request_id,
                decision=getattr(decision, "best_action", response.recommended_action).value,
                selected_plan=getattr(plan, "plan_type", "unknown"),
                confidence=response.confidence,
                outcome="prepared",
                metadata=dict(request.context),
            )
        )
        self.logger.info("reasoning_request request_id=%s", request.request_id)
        return response

    def statistics(self) -> ReasoningStatistics:
        self._ensure_initialized()
        return ReasoningStatistics(
            reasoning_status="ready" if self.engine.initialized else "unavailable",
            decision_status="ready" if self.engine.decision_engine.initialized else "unavailable",
            planning_status="ready" if self.engine.planning_engine.initialized else "unavailable",
            confidence_status="ready" if self.engine.confidence_engine.initialized else "unavailable",
            overall_intelligence_status="healthy",
        )

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReasoningManager must be initialized before use.")
