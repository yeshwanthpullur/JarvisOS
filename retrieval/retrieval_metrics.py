"""Retrieval metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class RetrievalMetrics:
    requests: int = 0
    successful_retrievals: int = 0
    failed_retrievals: int = 0
    average_retrieval_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    memory_queries: int = 0
    knowledge_queries: int = 0
    hybrid_queries: int = 0
    confidence_scores: float = 0.0
    ranking_statistics: int = 0

    def statistics(self) -> dict[str, float | int]:
        return asdict(self)
