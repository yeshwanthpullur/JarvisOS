"""Metrics placeholders for Agent Creator."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AgentCreatorMetrics:
    """Operational counters for Agent Creator."""

    generated_agents: int = 0
    installed_agents: int = 0
    validation_failures: int = 0
    rollback_plans: int = 0
    blueprints_registered: int = 0
    templates_registered: int = 0

