"""Metrics for reflection."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ReflectionMetrics:
    requests: int = 0
    successes: int = 0
    failures: int = 0
    patterns: int = 0
    improvements: int = 0

    def initialize(self) -> None:
        self.requests = 0
        self.successes = 0
        self.failures = 0
        self.patterns = 0
        self.improvements = 0
