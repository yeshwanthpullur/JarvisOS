"""Adaptive session model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from adaptive.adaptive_state import AdaptiveState


@dataclass(slots=True)
class AdaptiveSession:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    adaptive_id: str | None = None
    state: AdaptiveState = AdaptiveState.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
