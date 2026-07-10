"""Planning architecture for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from jarvis.jarvis_decision_engine import JarvisDecision


@dataclass(frozen=True, slots=True)
class JarvisPlanStep:
    """A planned step for future execution."""

    name: str
    description: str
    dependencies: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class JarvisExecutionPlan:
    """Execution plan metadata."""

    goal: str
    plan_id: str = field(default_factory=lambda: str(uuid4()))
    steps: tuple[JarvisPlanStep, ...] = ()
    fallback_strategy: str = "fallback"
    recovery_strategy: str = "recovery"
    estimated_execution_time_seconds: float = 0.0
    estimated_execution_cost: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)


class JarvisPlanning:
    """Builds deterministic plan shells."""

    initialized = True

    def create_plan(self, decision: JarvisDecision) -> JarvisExecutionPlan:
        """Create a plan shell for a decision."""
        step = JarvisPlanStep(
            name="prepare_response",
            description="Prepare an architecture-only executive response.",
        )
        return JarvisExecutionPlan(
            goal=decision.goal,
            steps=(step,),
            fallback_strategy=decision.recovery_strategy.value,
            recovery_strategy=decision.recovery_strategy.value,
        )

