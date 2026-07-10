"""Research history records."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field


@dataclass(slots=True)
class ResearchHistoryRecord:
    research_id: str
    topic: str
    strategy: str
    sources: tuple[str, ...] = ()
    workflow: str | None = None
    results: tuple[str, ...] = ()
    summary: str = ""
    references: tuple[str, ...] = ()
    duration_ms: float = 0.0
    confidence: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)


class ResearchHistory:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._records: list[ResearchHistoryRecord] = []
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("research_history_initialized")

    def record(self, record: ResearchHistoryRecord) -> None:
        self._ensure_initialized()
        self._records.append(record)
        self._logger.info("research_history_recorded research_id=%s", record.research_id)

    def count(self) -> int:
        self._ensure_initialized()
        return len(self._records)

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ResearchHistory must be initialized before use.")
