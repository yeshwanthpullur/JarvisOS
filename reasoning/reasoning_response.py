"""Reasoning response model."""

from __future__ import annotations

from dataclasses import dataclass, field

from reasoning.decision_engine import DecisionType


@dataclass(slots=True)
class ReasoningResponse:
    goal: str = ""
    intent: str = "unknown"
    missing_information: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()
    plans: tuple[str, ...] = ()
    recommended_action: DecisionType = DecisionType.ANSWER
    confidence: float = 0.0
    risk: float = 0.0
    cost: float = 0.0
    complexity: str = "unknown"
    metadata: dict[str, object] = field(default_factory=dict)
