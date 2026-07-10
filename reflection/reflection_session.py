"""Reflection session model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from reflection.reflection_state import ReflectionState


@dataclass(slots=True)
class ReflectionSession:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    reflection_id: str | None = None
    state: ReflectionState = ReflectionState.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
