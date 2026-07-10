"""Learning metadata capture for reflection."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReflectionLearningRecord:
    learning_id: str
    kind: str
    description: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


class ReflectionLearning:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.records: list[ReflectionLearningRecord] = []
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self.logger.info("reflection_learning_initialized")

    def capture(self, record: ReflectionLearningRecord) -> None:
        self._ensure_initialized()
        self.records.append(record)
        self.logger.info("learning_captured learning_id=%s", record.learning_id)

    def statistics(self) -> dict[str, Any]:
        self._ensure_initialized()
        return {"learning_records": len(self.records)}

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReflectionLearning must be initialized before use.")
