"""Reasoning plan model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ReasoningPlan:
    goal: str
    intent: str
    assumptions: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    required_systems: tuple[str, ...] = ()
    required_agents: tuple[str, ...] = ()
    required_providers: tuple[str, ...] = ()
    required_skills: tuple[str, ...] = ()
    required_plugins: tuple[str, ...] = ()
    execution_strategy: str = "direct"
    expected_outcome: str = ""
    confidence: float = 0.0
    risk: float = 0.0
    statistics: dict[str, object] = field(default_factory=dict)
