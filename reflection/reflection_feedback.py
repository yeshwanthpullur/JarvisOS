"""Feedback channel for Executive JARVIS."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReflectionFeedbackReport:
    recommendations: tuple[str, ...]
    confidence: tuple[float, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class ReflectionFeedback:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self.logger.info("reflection_feedback_initialized")

    def build(self, recommendations: tuple[str, ...]) -> ReflectionFeedbackReport:
        self._ensure_initialized()
        self.logger.info("reflection_feedback_built count=%s", len(recommendations))
        return ReflectionFeedbackReport(recommendations=recommendations)

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReflectionFeedback must be initialized before use.")
