"""Improvement suggestions for reflection."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReflectionImprovementItem:
    category: str
    recommendation: str
    confidence: float
    metadata: dict[str, Any] = field(default_factory=dict)


class ReflectionImprovement:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self.logger.info("reflection_improvement_initialized")

    def generate(self, categories: tuple[str, ...]) -> tuple[ReflectionImprovementItem, ...]:
        self._ensure_initialized()
        items = tuple(
            ReflectionImprovementItem(category=category, recommendation=f"Improve {category}.", confidence=0.8)
            for category in categories
        )
        self.logger.info("reflection_improvements_generated count=%s", len(items))
        return items

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReflectionImprovement must be initialized before use.")
