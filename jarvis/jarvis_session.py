"""Session metadata for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from jarvis.jarvis_types import SessionType
from jarvis.jarvis_utils import utc_now


@dataclass(slots=True)
class JarvisSession:
    """A session groups requests, goals, and execution metadata."""

    session_type: SessionType
    user_id: str = "local-user"
    session_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: object = field(default_factory=utc_now)
    ended_at: object | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def close(self) -> None:
        """Mark the session as ended."""
        self.ended_at = utc_now()

