"""Agent message model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4


class AgentMessageType(StrEnum):
    """Message type labels."""

    COMMAND = "command"
    QUERY = "query"
    RESPONSE = "response"
    EVENT = "event"
    TASK = "task"
    STATUS = "status"
    CUSTOM = "custom"


class AgentMessageStatus(StrEnum):
    """Message delivery status."""

    QUEUED = "queued"
    ROUTED = "routed"
    DELIVERED = "delivered"
    FAILED = "failed"


@dataclass(slots=True)
class AgentMessage:
    """Future distributed-compatible message envelope."""

    sender: str
    receiver: str
    payload: dict[str, Any] = field(default_factory=dict)
    message_type: AgentMessageType = AgentMessageType.CUSTOM
    priority: int = 100
    metadata: dict[str, Any] = field(default_factory=dict)
    correlation_id: str | None = None
    request_id: str | None = None
    timeout: timedelta | None = None
    retry_count: int = 0
    status: AgentMessageStatus = AgentMessageStatus.QUEUED
    message_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
