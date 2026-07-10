"""Metrics for adaptive intelligence."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AdaptiveMetrics:
    requests: int = 0
    approved: int = 0
    rejected: int = 0
    deferred: int = 0
    applied: int = 0

    def initialize(self) -> None:
        self.requests = self.approved = self.rejected = self.deferred = self.applied = 0
