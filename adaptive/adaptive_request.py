"""Request object for adaptive intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdaptiveRequest:
    adaptive_id: str
    reflection_id: str | None = None
    learning_id: str | None = None
    conversation_id: str | None = None
    reasoning_id: str | None = None
    workflow_id: str | None = None
    goal: str = ""
    intent: str = ""
    historical_metadata: dict[str, Any] = field(default_factory=dict)
    reflection_metadata: dict[str, Any] = field(default_factory=dict)
    learning_metadata: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    context: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
