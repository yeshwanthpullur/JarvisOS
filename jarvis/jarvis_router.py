"""Router for Executive JARVIS request pipeline."""

from __future__ import annotations

from jarvis.jarvis_decision_engine import JarvisDecision


class JarvisRouter:
    """Routes decisions to the correct executive subsystem metadata path."""

    initialized = True

    def route(self, decision: JarvisDecision) -> str:
        """Return a route key for a decision."""
        return decision.department or "executive"

