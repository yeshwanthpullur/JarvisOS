"""Adaptive history store."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdaptiveHistoryRecord:
    adaptive_id: str
    recommendation: str
    confidence: float
    improvement: float
    risk: float
    metadata: dict[str, Any] = field(default_factory=dict)


class AdaptiveHistory:
    def __init__(self) -> None:
        self.records: list[AdaptiveHistoryRecord] = []
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True

    def record(self, record: AdaptiveHistoryRecord) -> None:
        self._ensure_initialized()
        self.records.append(record)

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("AdaptiveHistory must be initialized before use.")
