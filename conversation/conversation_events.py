"""Conversation event models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4

from jarvis.jarvis_utils import utc_now


class ConversationEventType(StrEnum):
    """Conversation event types."""

    STARTED = "started"
    REQUEST_RECEIVED = "request_received"
    RESPONSE_READY = "response_ready"
    COMMAND_DISPATCHED = "command_dispatched"
    FAILED = "failed"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class ConversationEvent:
    """Conversation event envelope."""

    event_type: ConversationEventType
    conversation_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: object = field(default_factory=utc_now)

