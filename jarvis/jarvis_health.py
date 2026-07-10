"""Health model for Executive JARVIS."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from jarvis.jarvis_status import JarvisStatus
from jarvis.jarvis_utils import utc_now


@dataclass(slots=True)
class JarvisHealth:
    """Health state for Executive JARVIS."""

    status: JarvisStatus = JarvisStatus.HEALTHY
    last_heartbeat: object | None = None
    details: dict[str, Any] = field(default_factory=dict)

    def heartbeat(self) -> None:
        """Record heartbeat."""
        self.last_heartbeat = utc_now()
        self.status = JarvisStatus.HEALTHY

    def mark_failed(self, reason: str) -> None:
        """Mark the executive as failed."""
        self.status = JarvisStatus.FAILED
        self.details["reason"] = reason

