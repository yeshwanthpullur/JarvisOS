"""Reasoning context."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReasoningContext:
    request_id: str
    conversation_id: str | None = None
    workflow_id: str | None = None
    goal_id: str | None = None
    context: dict[str, object] = field(default_factory=dict)
