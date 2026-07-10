"""Manager for adaptive intelligence."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from adaptive.adaptive_context import AdaptiveContext
from adaptive.adaptive_diagnostics import AdaptiveDiagnostics
from adaptive.adaptive_engine import AdaptiveEngine
from adaptive.adaptive_history import AdaptiveHistory, AdaptiveHistoryRecord
from adaptive.adaptive_learning_queue import AdaptiveLearningQueue
from adaptive.adaptive_logger import AdaptiveLogger
from adaptive.adaptive_metrics import AdaptiveMetrics
from adaptive.adaptive_registry import AdaptiveRegistry
from adaptive.adaptive_request import AdaptiveRequest
from adaptive.adaptive_response import AdaptiveResponse
from adaptive.adaptive_validator import AdaptiveValidator


@dataclass(frozen=True, slots=True)
class AdaptiveStatistics:
    adaptive_status: str
    experience_status: str
    learning_queue_status: str
    policy_status: str
    rules_status: str
    overall_adaptive_health: str


class AdaptiveManager:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.engine = AdaptiveEngine(logger=self.logger)
        self.history = AdaptiveHistory()
        self.metrics = AdaptiveMetrics()
        self.diagnostics = AdaptiveDiagnostics()
        self.registry = AdaptiveRegistry()
        self.learning_queue = AdaptiveLearningQueue()
        self.adaptive_logger = AdaptiveLogger(logger=self.logger)
        self.validator = AdaptiveValidator()
        self.initialized = False

    def initialize(self) -> AdaptiveStatistics:
        self.engine.initialize()
        self.history.initialize()
        self.metrics.initialize()
        self.diagnostics.initialize()
        self.registry.initialize()
        self.learning_queue.initialize()
        self.adaptive_logger.initialize()
        self.validator.initialize()
        self.initialized = True
        self.logger.info("adaptive_manager_initialized")
        return self.statistics()

    def adapt(self, request: AdaptiveRequest, context: AdaptiveContext | None = None) -> AdaptiveResponse:
        self._ensure_initialized()
        response = self.engine.adapt(request, context)
        self.metrics.requests += 1
        self.history.record(
            AdaptiveHistoryRecord(
                adaptive_id=request.adaptive_id,
                recommendation=response.executive_recommendation,
                confidence=response.confidence,
                improvement=response.estimated_improvement,
                risk=response.estimated_risk,
                metadata=dict(request.context),
            )
        )
        return response

    def statistics(self) -> AdaptiveStatistics:
        self._ensure_initialized()
        return AdaptiveStatistics(
            adaptive_status="ready" if self.engine.initialized else "unavailable",
            experience_status="ready" if self.engine.experience.initialized else "unavailable",
            learning_queue_status="ready" if self.engine.queue.initialized else "unavailable",
            policy_status="ready",
            rules_status="ready" if self.engine.rules.initialized else "unavailable",
            overall_adaptive_health="healthy",
        )

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("AdaptiveManager must be initialized before use.")
