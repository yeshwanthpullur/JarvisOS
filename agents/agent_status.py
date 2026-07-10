"""Agent status definitions."""

from __future__ import annotations

from enum import StrEnum


class AgentStatus(StrEnum):
    """Operational status, separate from lifecycle state."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    INITIALIZING = "initializing"
    RUNNING = "running"
    IDLE = "idle"
    BUSY = "busy"
    PAUSED = "paused"
    RECOVERING = "recovering"
    STOPPED = "stopped"
    DISABLED = "disabled"
    FAILED = "failed"
