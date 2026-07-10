"""Retrieval history."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from retrieval.retrieval_strategy import RetrievalStrategy


@dataclass(frozen=True, slots=True)
class RetrievalHistoryRecord:
    retrieval_id: str
    request_id: str
    conversation_id: str | None
    workflow_id: str | None
    strategy: RetrievalStrategy
    sources_used: tuple[str, ...]
    retrieved_items: tuple[dict[str, Any], ...]
    execution_time_ms: float
    confidence: float
    statistics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class RetrievalHistory:
    initialized = True

    def __init__(self) -> None:
        self._records: list[RetrievalHistoryRecord] = []

    def append(self, record: RetrievalHistoryRecord) -> None:
        self._records.append(record)

    def list(self) -> tuple[RetrievalHistoryRecord, ...]:
        return tuple(self._records)

    def statistics(self) -> dict[str, int]:
        return {"retrievals": len(self._records)}
