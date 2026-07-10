"""Intent engine for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field

from jarvis.jarvis_capabilities import JarvisCapability
from jarvis.jarvis_request import JarvisRequest
from jarvis.jarvis_types import ExecutionStrategy, JarvisComplexity, JarvisIntentType


@dataclass(frozen=True, slots=True)
class IntentMetadata:
    """Intent analysis metadata."""

    primary_intent: JarvisIntentType
    secondary_intents: tuple[JarvisIntentType, ...] = ()
    confidence: float = 0.5
    complexity: JarvisComplexity = JarvisComplexity.UNKNOWN
    priority: int = 100
    required_systems: tuple[str, ...] = ()
    required_capabilities: tuple[JarvisCapability, ...] = ()
    required_departments: tuple[str, ...] = ()
    required_providers: tuple[str, ...] = ()
    execution_strategy: ExecutionStrategy = ExecutionStrategy.DIRECT
    metadata: dict[str, object] = field(default_factory=dict)


class JarvisIntentEngine:
    """Classifies requests without AI calls."""

    initialized = True

    def identify(self, request: JarvisRequest) -> IntentMetadata:
        """Return deterministic intent metadata for a request."""
        text = request.content.lower()
        intent = JarvisIntentType.CONVERSATION
        strategy = ExecutionStrategy.DIRECT
        capabilities: tuple[JarvisCapability, ...] = (JarvisCapability.CONVERSATION,)
        departments: tuple[str, ...] = ("executive",)
        if "create agent" in text or "agent creator" in text:
            intent = JarvisIntentType.AGENT_CREATION
            strategy = ExecutionStrategy.AGENT
            capabilities = (JarvisCapability.DELEGATION,)
            departments = ("engineering",)
        elif "plan" in text:
            intent = JarvisIntentType.PLANNING
            strategy = ExecutionStrategy.PLANNING
            capabilities = (JarvisCapability.PLANNING,)
            departments = ("planning",)
        elif "research" in text:
            intent = JarvisIntentType.RESEARCH
            strategy = ExecutionStrategy.RESEARCH
            capabilities = (JarvisCapability.KNOWLEDGE,)
            departments = ("research",)
        elif "memory" in text:
            intent = JarvisIntentType.MEMORY
            strategy = ExecutionStrategy.MEMORY
            capabilities = (JarvisCapability.MEMORY,)
            departments = ("memory",)
        elif "task" in text:
            intent = JarvisIntentType.TASK
            strategy = ExecutionStrategy.TASK
            capabilities = (JarvisCapability.TASKS,)
            departments = ("tasks",)
        complexity = JarvisComplexity.SIMPLE if len(text.split()) <= 12 else JarvisComplexity.MODERATE
        return IntentMetadata(
            primary_intent=intent,
            confidence=0.75 if intent is not JarvisIntentType.CONVERSATION else 0.6,
            complexity=complexity,
            priority=request.priority,
            required_systems=tuple(capability.value for capability in capabilities),
            required_capabilities=capabilities,
            required_departments=departments,
            execution_strategy=request.strategy_hint or strategy,
        )

