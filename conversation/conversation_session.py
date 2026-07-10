"""Conversation session metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from jarvis.jarvis_utils import utc_now


@dataclass(slots=True)
class ConversationSession:
    """Tracks one interactive conversation session."""

    conversation_id: str = field(default_factory=lambda: str(uuid4()))
    session_id: str = field(default_factory=lambda: str(uuid4()))
    request_id: str | None = None
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    trace_id: str = field(default_factory=lambda: str(uuid4()))
    current_topic: str | None = None
    current_goal: str | None = None
    current_workflow: str | None = None
    previous_requests: list[str] = field(default_factory=list)
    previous_responses: list[str] = field(default_factory=list)
    current_context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
    started_at: object = field(default_factory=utc_now)
    updated_at: object = field(default_factory=utc_now)

    def record(self, request: str, response: str) -> None:
        """Record a request and response."""
        self.previous_requests.append(request)
        self.previous_responses.append(response)
        self.updated_at = utc_now()

