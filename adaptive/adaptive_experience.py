"""Adaptive experience registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdaptiveExperienceRecord:
    experience_id: str
    experience_type: str
    description: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


class AdaptiveExperience:
    def __init__(self) -> None:
        self.records: dict[str, AdaptiveExperienceRecord] = {}
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True

    def register(self, record: AdaptiveExperienceRecord) -> None:
        self._ensure_initialized()
        self.records[record.experience_id] = record

    def validate(self, record: AdaptiveExperienceRecord) -> bool:
        self._ensure_initialized()
        return bool(record.experience_id and record.experience_type)

    def rank(self) -> tuple[AdaptiveExperienceRecord, ...]:
        self._ensure_initialized()
        return tuple(sorted(self.records.values(), key=lambda item: item.confidence, reverse=True))

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("AdaptiveExperience must be initialized before use.")
