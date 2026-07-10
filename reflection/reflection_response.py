"""Response object for reflection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReflectionResponse:
    reflection_report: str
    success_score: float
    failure_score: float
    confidence_score: float
    decision_quality: float
    planning_quality: float
    reasoning_quality: float
    execution_quality: float
    improvement_candidates: tuple[str, ...] = ()
    learning_candidates: tuple[str, ...] = ()
    memory_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    diagnostics: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
