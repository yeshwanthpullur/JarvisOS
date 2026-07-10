"""Confidence estimation."""

from __future__ import annotations

import logging


class ConfidenceEngine:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("confidence_engine_initialized")

    def determine(self, decision: float, knowledge: float, memory: float, research: float, execution: float) -> str:
        self._ensure_initialized()
        score = max(0.0, min(1.0, (decision + knowledge + memory + research + execution) / 5))
        if score < 0.2:
            return "very_low"
        if score < 0.4:
            return "low"
        if score < 0.7:
            return "medium"
        if score < 0.9:
            return "high"
        return "very_high"

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ConfidenceEngine must be initialized before use.")
