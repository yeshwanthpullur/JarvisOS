"""Conversation request model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jarvis import ExecutionStrategy
from jarvis.jarvis_types import JarvisComplexity, JarvisIntentType
from jarvis.jarvis_utils import utc_now


@dataclass(frozen=True, slots=True)
class ConversationRequest:
    """Normalized user input entering the conversation engine."""

    user_input: str
    normalized_input: str
    timestamp: object = field(default_factory=utc_now)
    intent: JarvisIntentType = JarvisIntentType.UNKNOWN
    goal: str = ""
    priority: int = 100
    complexity: JarvisComplexity = JarvisComplexity.UNKNOWN
    execution_strategy: ExecutionStrategy = ExecutionStrategy.DIRECT
    department: str | None = None
    agent: str | None = None
    provider: str | None = None
    plugins: tuple[str, ...] = ()
    tools: tuple[str, ...] = ()
    skills: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

