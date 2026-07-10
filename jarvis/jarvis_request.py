"""Request model for the Executive JARVIS Core."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from jarvis.jarvis_types import ExecutionStrategy
from jarvis.jarvis_utils import utc_now


@dataclass(frozen=True, slots=True)
class JarvisRequest:
    """User or system request entering JARVIS first."""

    content: str
    user_id: str = "local-user"
    request_id: str = field(default_factory=lambda: str(uuid4()))
    conversation_id: str | None = None
    priority: int = 100
    strategy_hint: ExecutionStrategy | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: object = field(default_factory=utc_now)

