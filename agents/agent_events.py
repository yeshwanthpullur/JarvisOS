"""Agent event model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class AgentEventCategory(StrEnum):
    """Agent event categories."""

    LIFECYCLE = "lifecycle"
    SCHEDULER = "scheduler"
    HEALTH = "health"
    MESSAGE = "message"
    TASK = "task"
    PROVIDER = "provider"
    PLUGIN = "plugin"
    CHECKPOINT = "checkpoint"
    METRICS = "metrics"
    CUSTOM = "custom"


@dataclass(frozen=True, slots=True)
class AgentEvent:
    """Standard event emitted by the agent framework."""

    source: str
    category: AgentEventCategory
    target: str | None = None
    priority: int = 100
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
