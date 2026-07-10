"""Queue for adaptive learning candidates."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AdaptiveQueueState(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    APPLIED = "applied"
    EXPIRED = "expired"


@dataclass(slots=True)
class AdaptiveQueueEntry:
    entry_id: str
    adaptive_id: str
    state: AdaptiveQueueState = AdaptiveQueueState.PENDING
    priority: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class AdaptiveLearningQueue:
    def __init__(self) -> None:
        self.entries: list[AdaptiveQueueEntry] = []
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True

    def enqueue(self, entry: AdaptiveQueueEntry) -> None:
        self._ensure_initialized()
        self.entries.append(entry)
        self.entries.sort(key=lambda item: item.priority, reverse=True)

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("AdaptiveLearningQueue must be initialized before use.")
