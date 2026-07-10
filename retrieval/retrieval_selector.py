"""Retrieval selector."""

from __future__ import annotations

from retrieval.retrieval_request import RetrievalRequest
from retrieval.retrieval_strategy import RetrievalStrategy


class RetrievalSelector:
    initialized = True

    def determine_sources(self, request: RetrievalRequest) -> tuple[str, ...]:
        if request.required_sources:
            return request.required_sources
        if request.retrieval_strategy is RetrievalStrategy.MEMORY_FIRST:
            return ("memory", "knowledge")
        if request.retrieval_strategy is RetrievalStrategy.KNOWLEDGE_FIRST:
            return ("knowledge", "memory")
        return ("memory", "knowledge")

    def determine_search_order(self, sources: tuple[str, ...]) -> tuple[str, ...]:
        return sources

    def determine_search_depth(self, request: RetrievalRequest) -> int:
        return 1 if request.retrieval_strategy is RetrievalStrategy.EXACT_MATCH else 2

    def determine_retrieval_strategy(self, request: RetrievalRequest) -> RetrievalStrategy:
        return request.retrieval_strategy

    def determine_ranking_strategy(self, request: RetrievalRequest) -> str:
        return "recency" if request.retrieval_strategy is RetrievalStrategy.RECENT_FIRST else "relevance"

    def estimate_confidence(self, request: RetrievalRequest) -> float:
        return 0.9 if request.query else 0.0

    def optimize_retrieval(self, request: RetrievalRequest) -> RetrievalRequest:
        return request
