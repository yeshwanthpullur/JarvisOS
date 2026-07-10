"""Research manager for JARVIS OS."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from research.research_context import ResearchContext
from research.research_diagnostics import ResearchDiagnostics
from research.research_engine import ResearchEngine
from research.research_history import ResearchHistory, ResearchHistoryRecord
from research.research_logger import ResearchLogger
from research.research_metrics import ResearchMetrics
from research.research_request import ResearchRequest
from research.research_response import ResearchResponse


@dataclass(frozen=True, slots=True)
class ResearchStatistics:
    research_engine_status: str
    learning_engine_status: str
    knowledge_builder_status: str
    research_sources: int
    overall_research_health: str


class ResearchManager:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.engine = ResearchEngine(logger=self.logger)
        self.history = ResearchHistory(logger=self.logger)
        self.metrics = ResearchMetrics()
        self.diagnostics = ResearchDiagnostics()
        self.research_logger = ResearchLogger(logger=self.logger)
        self.initialized = False

    def initialize(self) -> ResearchStatistics:
        self.engine.initialize()
        self.history.initialize()
        self.metrics.initialize()
        self.diagnostics.initialize()
        self.initialized = True
        self.logger.info("research_manager_initialized")
        return self.statistics()

    def research(self, request: ResearchRequest, context: ResearchContext | None = None) -> ResearchResponse:
        self._ensure_initialized()
        response = self.engine.execute(request, context)
        self.metrics.requests += 1
        self.metrics.completed += 1
        self.history.record(
            ResearchHistoryRecord(
                research_id=request.request_id,
                topic=request.topic,
                strategy=request.strategy.value,
                sources=request.sources,
                workflow=context.workflow_id if context else None,
                results=response.findings,
                summary=response.summary,
                references=response.references,
                confidence=response.confidence,
                metadata=dict(request.metadata),
            )
        )
        self.logger.info("research_request request_id=%s topic=%s", request.request_id, request.topic)
        return response

    def statistics(self) -> ResearchStatistics:
        self._ensure_initialized()
        return ResearchStatistics(
            research_engine_status="ready" if self.engine.initialized else "unavailable",
            learning_engine_status="ready" if self.engine.learning_engine.initialized else "unavailable",
            knowledge_builder_status="ready" if self.engine.knowledge_builder.initialized else "unavailable",
            research_sources=8,
            overall_research_health="healthy",
        )

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ResearchManager must be initialized before use.")
