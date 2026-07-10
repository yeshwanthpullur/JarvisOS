"""Reasoning history records."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field


@dataclass(slots=True)
class ReasoningHistoryRecord:
    request_id: str
    decision: str
    selected_plan: str
    rejected_plans: tuple[str, ...] = ()
    reasoning_strategy: str = "direct"
    confidence: float = 0.0
    outcome: str = "unknown"
    execution_result: str = ""
    failures: tuple[str, ...] = ()
    recovery: str = ""
    lessons_learned: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


class ReasoningHistory:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._records: list[ReasoningHistoryRecord] = []
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("reasoning_history_initialized")

    def record(self, record: ReasoningHistoryRecord) -> None:
        self._ensure_initialized()
        self._records.append(record)
        self._logger.info("reasoning_history_recorded request_id=%s", record.request_id)

    def count(self) -> int:
        self._ensure_initialized()
        return len(self._records)

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReasoningHistory must be initialized before use.")
