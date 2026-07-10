"""Request object for reflection."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ReflectionRequest:
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
    execution_metadata: dict[str, Any] = field(default_factory=dict)
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    reasoning_metadata: dict[str, Any] = field(default_factory=dict)
    planning_metadata: dict[str, Any] = field(default_factory=dict)
    workflow_metadata: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
