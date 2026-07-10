"""Orchestrator for Executive JARVIS."""

from __future__ import annotations

from jarvis.jarvis_decision_engine import JarvisDecision
from jarvis.jarvis_planning import JarvisExecutionPlan


class JarvisOrchestrator:
    """Coordinates future multi-system workflows without executing them."""

    initialized = True

    def coordinate(self, decision: JarvisDecision, plan: JarvisExecutionPlan) -> dict[str, object]:
        """Return orchestration metadata."""
        return {"strategy": decision.strategy.value, "steps": len(plan.steps)}

