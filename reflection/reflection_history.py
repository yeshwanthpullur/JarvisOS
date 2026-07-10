"""Reflection history store."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReflectionHistoryRecord:
    reflection_id: str
    success_score: float
    failure_score: float
    confidence_score: float
    summary: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ReflectionHistory:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.records: list[ReflectionHistoryRecord] = []
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self.logger.info("reflection_history_initialized")

    def record(self, record: ReflectionHistoryRecord) -> None:
        self._ensure_initialized()
        self.records.append(record)
        self.logger.info("reflection_history_recorded reflection_id=%s", record.reflection_id)

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReflectionHistory must be initialized before use.")
