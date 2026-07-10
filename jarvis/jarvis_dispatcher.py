"""Delegation dispatcher for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field

from jarvis.jarvis_decision_engine import JarvisDecision
from jarvis.jarvis_planning import JarvisExecutionPlan
from jarvis.jarvis_types import DelegationType


@dataclass(frozen=True, slots=True)
class DispatchResult:
    """Result returned by dispatcher architecture."""

    delegation_type: DelegationType
    selected_department: str | None
    selected_agent: str | None = None
    selected_provider: str | None = None
    success: bool = True
    results: tuple[str, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)


class JarvisDispatcher:
    """Selects future delegation targets without executing work."""

    initialized = True

    def dispatch(self, decision: JarvisDecision, plan: JarvisExecutionPlan) -> DispatchResult:
        """Prepare dispatch metadata."""
        return DispatchResult(
            delegation_type=DelegationType.SINGLE_AGENT,
            selected_department=decision.department,
            selected_agent=decision.agent,
            selected_provider=decision.provider,
            results=(f"planned_steps={len(plan.steps)}",),
        )

