"""Context shared by the reflection subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReflectionContext:
    reflection_id: str
    conversation_id: str | None = None
    execution_id: str | None = None
    reasoning_id: str | None = None
    planning_id: str | None = None
    workflow_id: str | None = None
    goal: str = ""
    intent: str = ""
    expected_outcome: str = ""
    actual_outcome: str = ""
    memory_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    statistics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
