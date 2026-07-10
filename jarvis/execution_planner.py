"""Execution planner for the conversation pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    """Execution plan metadata."""

    strategy: str
    steps: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


class ExecutionPlanner:
    """Plans execution strategy without executing work."""

    initialized = True

    def plan(self, strategy: str = "direct") -> ExecutionPlan:
        """Return execution plan."""
        return ExecutionPlan(strategy=strategy, steps=("dispatch", "compose_response"))

