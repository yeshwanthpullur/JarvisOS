"""Reasoning goal model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReasoningGoal:
    goal: str
    assumptions: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)
