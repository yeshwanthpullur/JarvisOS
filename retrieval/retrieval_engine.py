"""Retrieval engine."""

from __future__ import annotations

import time
from dataclasses import dataclass, asdict
from typing import Any

from retrieval.retrieval_cache import RetrievalCache
from retrieval.retrieval_context import RetrievalContext
from retrieval.retrieval_diagnostics import RetrievalDiagnostics
from retrieval.retrieval_history import RetrievalHistory, RetrievalHistoryRecord
from retrieval.retrieval_metrics import RetrievalMetrics
from retrieval.retrieval_ranker import RetrievalRanker
from retrieval.retrieval_request import RetrievalRequest
from retrieval.retrieval_response import RetrievalResponse
from retrieval.retrieval_selector import RetrievalSelector
from retrieval.retrieval_strategy import RetrievalStrategy
from retrieval.retrieval_validator import RetrievalValidator


@dataclass(frozen=True, slots=True)
class RetrievalExecutionResult:
    retrieved_items: tuple[dict[str, Any], ...]
    memory_references: tuple[str, ...]
    knowledge_references: tuple[str, ...]
    conversation_references: tuple[str, ...]
    task_references: tuple[str, ...]
    workflow_references: tuple[str, ...]
    confidence: float
    statistics: dict[str, Any]
    metadata: dict[str, Any]


class RetrievalEngine:
    initialized = True

    def __init__(
        self,
        selector: RetrievalSelector | None = None,
        ranker: RetrievalRanker | None = None,
        cache: RetrievalCache | None = None,
        history: RetrievalHistory | None = None,
        metrics: RetrievalMetrics | None = None,
        validator: RetrievalValidator | None = None,
        diagnostics: RetrievalDiagnostics | None = None,
    ) -> None:
        self.selector = selector or RetrievalSelector()
        self.ranker = ranker or RetrievalRanker()
        self.cache = cache or RetrievalCache()
        self.history = history or RetrievalHistory()
        self.metrics = metrics or RetrievalMetrics()
        self.validator = validator or RetrievalValidator()
        self.diagnostics = diagnostics or RetrievalDiagnostics()

    def retrieve(self, request: RetrievalRequest, context: RetrievalContext) -> RetrievalResponse:
        start = time.perf_counter()
        valid, issues = self.validator.validate_request(request)
        if not valid:
            self.metrics.failed_retrievals += 1
            return RetrievalResponse(metadata={"errors": issues})
        sources = self.selector.determine_sources(request)
        ordered_sources = self.selector.determine_search_order(sources)
        items = self._query_sources(ordered_sources, request, context)
        ranked = self.ranker.rank(items, context=context)
        confidence = self.selector.estimate_confidence(request)
        response = RetrievalResponse(
            retrieved_items=ranked,
            memory_references=tuple(item.get("reference", "") for item in ranked if item.get("source") == "memory"),
            knowledge_references=tuple(item.get("reference", "") for item in ranked if item.get("source") == "knowledge"),
            conversation_references=tuple(item.get("reference", "") for item in ranked if item.get("source") == "conversation"),
            task_references=tuple(item.get("reference", "") for item in ranked if item.get("source") == "task"),
            workflow_references=tuple(item.get("reference", "") for item in ranked if item.get("source") == "workflow"),
            confidence=confidence,
            statistics={"sources_used": ordered_sources},
            metadata={"strategy": request.retrieval_strategy.value},
        )
        self.metrics.requests += 1
        self.metrics.successful_retrievals += 1
        elapsed_ms = (time.perf_counter() - start) * 1000
        self.history.append(
            RetrievalHistoryRecord(
                retrieval_id=request.request_id,
                request_id=request.request_id,
                conversation_id=request.conversation_id,
                workflow_id=request.workflow_id,
                strategy=request.retrieval_strategy,
                sources_used=ordered_sources,
                retrieved_items=ranked,
                execution_time_ms=elapsed_ms,
                confidence=confidence,
                statistics=response.statistics,
                metadata=response.metadata,
            )
        )
        self.cache.create("recent_queries", request.request_id, request.query)
        self.cache.create("recent_results", request.request_id, response)
        return response

    def _query_sources(
        self,
        sources: tuple[str, ...],
        request: RetrievalRequest,
        context: RetrievalContext,
    ) -> tuple[dict[str, Any], ...]:
        results: list[dict[str, Any]] = []
        if "memory" in sources:
            if context.memory_manager is not None:
                try:
                    memories = context.memory_manager.search_memory(
                        request.query,
                        tags=("personal-intelligence",),
                        limit=5,
                    )
                    for memory in memories:
                        results.append(
                            {
                                "source": "memory",
                                "reference": f"memory:{memory.id}",
                                "priority": memory.importance,
                                "confidence": memory.metadata.get("personal_intelligence", {}).get("confidence", 0.5),
                                "classification": memory.metadata.get("personal_intelligence", {}).get("classification", "derived"),
                                "active": memory.metadata.get("personal_intelligence", {}).get("active", True),
                                "content": memory.content,
                                "metadata": memory.metadata,
                            }
                        )
                except Exception:
                    results.append({"source": "memory", "reference": "memory:1", "priority": 2, "content": request.query})
            else:
                results.append({"source": "memory", "reference": "memory:1", "priority": 2, "content": request.query})
        if "knowledge" in sources:
            results.append({"source": "knowledge", "reference": "knowledge:1", "priority": 2, "content": request.query})
        if "conversation" in sources and context.conversation_history is not None:
            results.append({"source": "conversation", "reference": "conversation:1", "priority": 1, "content": request.query})
        if "workflow" in sources and context.workflow_history is not None:
            results.append({"source": "workflow", "reference": "workflow:1", "priority": 1, "content": request.query})
        if "task" in sources and context.task_history is not None:
            results.append({"source": "task", "reference": "task:1", "priority": 1, "content": request.query})
        if "provider" in sources and context.provider_history is not None:
            results.append({"source": "provider", "reference": "provider:1", "priority": 1, "content": request.query})
        if "plugin" in sources and context.plugin_history is not None:
            results.append({"source": "plugin", "reference": "plugin:1", "priority": 1, "content": request.query})
        if "execution" in sources and context.execution_history is not None:
            results.append({"source": "execution", "reference": "execution:1", "priority": 1, "content": request.query})
        return tuple(results)
