"""Pattern store for reflection learning."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReflectionPatternRecord:
    pattern_id: str
    pattern_type: str
    description: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


class ReflectionPatterns:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.records: dict[str, ReflectionPatternRecord] = {}
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self.logger.info("reflection_patterns_initialized")

    def register(self, record: ReflectionPatternRecord) -> None:
        self._ensure_initialized()
        self.records[record.pattern_id] = record
        self.logger.info("pattern_registered pattern_id=%s", record.pattern_id)

    def update(self, record: ReflectionPatternRecord) -> None:
        self.register(record)

    def remove(self, pattern_id: str) -> None:
        self._ensure_initialized()
        self.records.pop(pattern_id, None)
        self.logger.info("pattern_removed pattern_id=%s", pattern_id)

    def lookup(self, pattern_id: str) -> ReflectionPatternRecord | None:
        self._ensure_initialized()
        return self.records.get(pattern_id)

    def search(self, pattern_type: str) -> tuple[ReflectionPatternRecord, ...]:
        self._ensure_initialized()
        return tuple(record for record in self.records.values() if record.pattern_type == pattern_type)

    def rank(self) -> tuple[ReflectionPatternRecord, ...]:
        self._ensure_initialized()
        return tuple(sorted(self.records.values(), key=lambda record: record.confidence, reverse=True))

    def validate(self, record: ReflectionPatternRecord) -> bool:
        self._ensure_initialized()
        return bool(record.pattern_id and record.pattern_type and record.description)

    def statistics(self) -> dict[str, Any]:
        self._ensure_initialized()
        return {"patterns": len(self.records)}

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReflectionPatterns must be initialized before use.")
