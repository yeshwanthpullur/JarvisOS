"""Conversation lifecycle states."""

from __future__ import annotations

from enum import StrEnum


class ConversationState(StrEnum):
    """Conversation states managed by the conversation engine."""

    CREATED = "created"
    ACTIVE = "active"
    WAITING = "waiting"
    PROCESSING = "processing"
    DELEGATING = "delegating"
    RESPONDING = "responding"
    PAUSED = "paused"
    RECOVERED = "recovered"
    COMPLETED = "completed"
    CLOSED = "closed"
    FAILED = "failed"

