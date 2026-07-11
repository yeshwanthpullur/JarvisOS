"""Shared models for context intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class ContextItem:
    """Minimal contextual reference tracked across turns."""

    identifier: str = field(default_factory=lambda: str(uuid4()))
    context_type: str = "objective"
    value: str = ""
    scope: str = "conversation"
    source: str = "conversation"
    source_reference: str | None = None
    confidence: float = 0.5
    created_time: datetime = field(default_factory=utc_now)
    updated_time: datetime = field(default_factory=utc_now)
    last_active_time: datetime = field(default_factory=utc_now)
    expires_at: datetime | None = None
    active: bool = True
    priority: int = 100
    parent_context: str | None = None
    related_context: tuple[str, ...] = ()
    resolution_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ContextResolution:
    """Structured outcome for a context lookup or continuation attempt."""

    request_type: str
    status: str
    confidence: float = 0.0
    resolved_item: ContextItem | None = None
    candidates: tuple[ContextItem, ...] = ()
    reason: str = ""
    suggested_clarification: str | None = None
    active_objective: str | None = None
    pending_state: dict[str, Any] = field(default_factory=dict)
    next_step: str | None = None
    immediate_response: str | None = None
    ambiguity: bool = False
    stale_reference: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
