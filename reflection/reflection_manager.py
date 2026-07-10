"""Manager for reflection and learning."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from reflection.reflection_context import ReflectionContext
from reflection.reflection_diagnostics import ReflectionDiagnostics
from reflection.reflection_engine import ReflectionEngine
from reflection.reflection_history import ReflectionHistory, ReflectionHistoryRecord
from reflection.reflection_logger import ReflectionLogger
from reflection.reflection_metrics import ReflectionMetrics
from reflection.reflection_registry import ReflectionRegistry
from reflection.reflection_request import ReflectionRequest
from reflection.reflection_response import ReflectionResponse
from reflection.reflection_validator import ReflectionValidator


@dataclass(frozen=True, slots=True)
class ReflectionStatistics:
    reflection_status: str
    learning_status: str
    pattern_status: str
    confidence_status: str
    improvement_status: str
    overall_reflection_health: str


class ReflectionManager:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.engine = ReflectionEngine(logger=self.logger)
        self.history = ReflectionHistory(logger=self.logger)
        self.metrics = ReflectionMetrics()
        self.diagnostics = ReflectionDiagnostics()
        self.registry = ReflectionRegistry(logger=self.logger)
        self.reflection_logger = ReflectionLogger(logger=self.logger)
        self.validator = ReflectionValidator(logger=self.logger)
        self.initialized = False

    def initialize(self) -> ReflectionStatistics:
        self.engine.initialize()
        self.history.initialize()
        self.metrics.initialize()
        self.diagnostics.initialize()
        self.registry.initialize()
        self.reflection_logger.initialize()
        self.validator.initialize()
        self.initialized = True
        self.logger.info("reflection_manager_initialized")
        return self.statistics()

    def reflect(self, request: ReflectionRequest, context: ReflectionContext | None = None) -> ReflectionResponse:
        self._ensure_initialized()
        response = self.engine.reflect(request, context)
        self.metrics.requests += 1
        self.metrics.successes += 1
        self.metrics.patterns = len(self.engine.patterns.records)
        self.history.record(
            ReflectionHistoryRecord(
                reflection_id=request.reflection_id,
                success_score=response.success_score,
                failure_score=response.failure_score,
                confidence_score=response.confidence_score,
                summary=response.reflection_report,
                metadata=dict(request.metadata),
            )
        )
        self.logger.info("reflection_request reflection_id=%s", request.reflection_id)
        return response

    def statistics(self) -> ReflectionStatistics:
        self._ensure_initialized()
        return ReflectionStatistics(
            reflection_status="ready" if self.engine.initialized else "unavailable",
            learning_status="ready" if self.engine.learning.initialized else "unavailable",
            pattern_status="ready" if self.engine.patterns.initialized else "unavailable",
            confidence_status="ready" if self.engine.confidence.initialized else "unavailable",
            improvement_status="ready" if self.engine.improvement.initialized else "unavailable",
            overall_reflection_health="healthy",
        )

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReflectionManager must be initialized before use.")
