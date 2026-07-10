"""Context shared by adaptive intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdaptiveContext:
    adaptive_id: str
    reflection_id: str | None = None
    learning_id: str | None = None
    conversation_id: str | None = None
    reasoning_id: str | None = None
    workflow_id: str | None = None
    goal: str = ""
    intent: str = ""
    confidence: float = 0.0
    memory_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    statistics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
