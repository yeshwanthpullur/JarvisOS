"""Decision engine for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field

from jarvis.jarvis_intent_engine import IntentMetadata
from jarvis.jarvis_types import ExecutionStrategy, JarvisComplexity


@dataclass(frozen=True, slots=True)
class JarvisDecision:
    """Decision metadata produced before planning and dispatch."""

    goal: str
    complexity: JarvisComplexity
    confidence: float
    priority: int
    strategy: ExecutionStrategy
    department: str | None = None
    agent: str | None = None
    provider: str | None = None
    plugin: str | None = None
    tool: str | None = None
    skill: str | None = None
    workflow: str | None = None
    recovery_strategy: ExecutionStrategy = ExecutionStrategy.RECOVERY
    metadata: dict[str, object] = field(default_factory=dict)


class JarvisDecisionEngine:
    """Chooses executive strategy from intent metadata."""

    initialized = True

    def decide(self, request_content: str, intent: IntentMetadata) -> JarvisDecision:
        """Return a decision without executing external work."""
        department = intent.required_departments[0] if intent.required_departments else "executive"
        return JarvisDecision(
            goal=request_content.strip() or "Handle empty request",
            complexity=intent.complexity,
            confidence=intent.confidence,
            priority=intent.priority,
            strategy=intent.execution_strategy,
            department=department,
            agent=None,
            provider=None,
            workflow="future_workflow" if intent.execution_strategy is ExecutionStrategy.WORKFLOW else None,
        )

