"""Retrieval manager."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from retrieval.retrieval_cache import RetrievalCache
from retrieval.retrieval_context import RetrievalContext
from retrieval.retrieval_diagnostics import RetrievalDiagnostics
from retrieval.retrieval_engine import RetrievalEngine
from retrieval.retrieval_history import RetrievalHistory
from retrieval.retrieval_logger import RetrievalLogger
from retrieval.retrieval_metrics import RetrievalMetrics
from retrieval.retrieval_ranker import RetrievalRanker
from retrieval.retrieval_request import RetrievalRequest
from retrieval.retrieval_response import RetrievalResponse
from retrieval.retrieval_selector import RetrievalSelector
from retrieval.retrieval_strategy import RetrievalStrategy
from retrieval.retrieval_validator import RetrievalValidator


@dataclass(frozen=True, slots=True)
class RetrievalStatistics:
    retrieval_engine_status: str
    available_retrieval_sources: int
    cache_status: str
    ranking_status: str
    overall_retrieval_health: str


class RetrievalManager:
    initialized = True

    def __init__(
        self,
        context: RetrievalContext | None = None,
        engine: RetrievalEngine | None = None,
        selector: RetrievalSelector | None = None,
        ranker: RetrievalRanker | None = None,
        cache: RetrievalCache | None = None,
        history: RetrievalHistory | None = None,
        metrics: RetrievalMetrics | None = None,
        validator: RetrievalValidator | None = None,
        diagnostics: RetrievalDiagnostics | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.context = context or RetrievalContext()
        self.selector = selector or RetrievalSelector()
        self.ranker = ranker or RetrievalRanker()
        self.cache = cache or RetrievalCache()
        self.history = history or RetrievalHistory()
        self.metrics = metrics or RetrievalMetrics()
        self.validator = validator or RetrievalValidator()
        self.diagnostics = diagnostics or RetrievalDiagnostics()
        self.engine = engine or RetrievalEngine(
            selector=self.selector,
            ranker=self.ranker,
            cache=self.cache,
            history=self.history,
            metrics=self.metrics,
            validator=self.validator,
            diagnostics=self.diagnostics,
        )
        self.logger = logger or self.context.logger
        self.logger_factory = RetrievalLogger(self.logger)

    def initialize(self) -> RetrievalStatistics:
        self.logger.info("retrieval_engine_initialized")
        return self.statistics()

    def retrieve(self, request: RetrievalRequest) -> RetrievalResponse:
        response = self.engine.retrieve(request, self.context)
        self.logger.info("retrieval_request request_id=%s confidence=%s", request.request_id, response.confidence)
        return response

    def statistics(self) -> RetrievalStatistics:
        return RetrievalStatistics(
            retrieval_engine_status="ready" if self.engine.initialized else "unavailable",
            available_retrieval_sources=8,
            cache_status="ready" if self.cache.initialized else "unavailable",
            ranking_status="ready" if self.ranker.initialized else "unavailable",
            overall_retrieval_health="healthy",
        )
