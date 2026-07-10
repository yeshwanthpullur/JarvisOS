"""Operational status values for Executive JARVIS components."""

from __future__ import annotations

from enum import StrEnum


class JarvisStatus(StrEnum):
    """Status values separate from runtime state."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    IDLE = "idle"
    BUSY = "busy"
    PAUSED = "paused"
    RECOVERING = "recovering"
    STOPPED = "stopped"
    FAILED = "failed"

