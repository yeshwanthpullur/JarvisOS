"""Confidence analysis for reflection."""

from __future__ import annotations

import logging
from dataclasses import dataclass


@dataclass(slots=True)
class ReflectionConfidenceReport:
    expected_confidence: float
    actual_confidence: float
    confidence_error: float
    confidence_drift: float
    decision_reliability: float
    planning_reliability: float
    reasoning_reliability: float
    retrieval_reliability: float
    research_reliability: float
    workflow_reliability: float
    learning_reliability: float
    summary: str


class ReflectionConfidence:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self.logger.info("reflection_confidence_initialized")

    def measure(self, expected: float, actual: float) -> ReflectionConfidenceReport:
        self._ensure_initialized()
        error = abs(expected - actual)
        drift = actual - expected
        report = ReflectionConfidenceReport(
            expected_confidence=expected,
            actual_confidence=actual,
            confidence_error=error,
            confidence_drift=drift,
            decision_reliability=max(0.0, 1.0 - error),
            planning_reliability=max(0.0, 1.0 - error / 2),
            reasoning_reliability=max(0.0, 1.0 - error / 2),
            retrieval_reliability=0.85,
            research_reliability=0.85,
            workflow_reliability=0.9,
            learning_reliability=0.9,
            summary="Confidence measured.",
        )
        self.logger.info("reflection_confidence_measured")
        return report

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReflectionConfidence must be initialized before use.")
