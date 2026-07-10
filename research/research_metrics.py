"""Research metrics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ResearchMetricsSnapshot:
    requests: int = 0
    completed: int = 0
    failed: int = 0


class ResearchMetrics:
    def __init__(self) -> None:
        self.initialized = False
        self.requests = 0
        self.completed = 0
        self.failed = 0

    def initialize(self) -> None:
        self.initialized = True

    def snapshot(self) -> ResearchMetricsSnapshot:
        if not self.initialized:
            raise RuntimeError("ResearchMetrics must be initialized before use.")
        return ResearchMetricsSnapshot(self.requests, self.completed, self.failed)
