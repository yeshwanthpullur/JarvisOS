"""Event models for the Executive JARVIS Core."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4

from jarvis.jarvis_utils import utc_now


class JarvisEventType(StrEnum):
    """Executive event types."""

    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    RESTART = "restart"
    PAUSE = "pause"
    RESUME = "resume"
    CONVERSATION_STARTED = "conversation_started"
    CONVERSATION_ENDED = "conversation_ended"
    REQUEST_RECEIVED = "request_received"
    INTENT_IDENTIFIED = "intent_identified"
    DECISION_COMPLETED = "decision_completed"
    PLANNING_COMPLETED = "planning_completed"
    DELEGATION_STARTED = "delegation_started"
    DELEGATION_COMPLETED = "delegation_completed"
    RESPONSE_GENERATED = "response_generated"
    HEALTH_CHANGED = "health_changed"
    CHECKPOINT_CREATED = "checkpoint_created"
    RECOVERY_COMPLETED = "recovery_completed"
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class JarvisEvent:
    """Event envelope with distributed-ready metadata."""

    event_type: JarvisEventType
    source: str
    payload: dict[str, Any] = field(default_factory=dict)
    target: str | None = None
    priority: int = 100
    correlation_id: str | None = None
    execution_id: str | None = None
    request_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: object = field(default_factory=utc_now)

