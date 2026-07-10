"""Agent health model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from agents.agent_status import AgentStatus


def utc_now() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class AgentHealth:
    """Health state exposed by each agent."""

    status: AgentStatus = AgentStatus.HEALTHY
    last_heartbeat: datetime | None = None
    uptime_seconds: float = 0.0
    downtime_seconds: float = 0.0
    restart_count: int = 0
    failure_count: int = 0
    recovery_count: int = 0
    details: dict[str, Any] = field(default_factory=dict)

    def heartbeat(self) -> None:
        """Record a heartbeat."""
        self.last_heartbeat = utc_now()
        self.status = AgentStatus.HEALTHY

    def mark_failed(self, error: str) -> None:
        """Mark the agent unhealthy."""
        self.failure_count += 1
        self.status = AgentStatus.FAILED
        self.details["last_error"] = error
