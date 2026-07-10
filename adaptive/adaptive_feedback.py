"""Feedback channel for executive review."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdaptiveFeedbackReport:
    recommendations: tuple[str, ...]
    confidence: tuple[float, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class AdaptiveFeedback:
    def __init__(self) -> None:
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True

    def build(self, recommendations: tuple[str, ...]) -> AdaptiveFeedbackReport:
        self._ensure_initialized()
        return AdaptiveFeedbackReport(recommendations=recommendations)

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("AdaptiveFeedback must be initialized before use.")
