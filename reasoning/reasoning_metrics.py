"""Reasoning metrics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReasoningMetricsSnapshot:
    requests: int = 0
    decisions: int = 0
    plans: int = 0


class ReasoningMetrics:
    def __init__(self) -> None:
        self.initialized = False
        self.requests = 0
        self.decisions = 0
        self.plans = 0

    def initialize(self) -> None:
        self.initialized = True

    def snapshot(self) -> ReasoningMetricsSnapshot:
        if not self.initialized:
            raise RuntimeError("ReasoningMetrics must be initialized before use.")
        return ReasoningMetricsSnapshot(self.requests, self.decisions, self.plans)
