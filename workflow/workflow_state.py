"""Workflow lifecycle state definitions."""

from __future__ import annotations

from enum import StrEnum


class WorkflowState(StrEnum):
    CREATED = "created"
    INITIALIZED = "initialized"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    RESUMED = "resumed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RECOVERED = "recovered"
    FAILED = "failed"


class WorkflowStatus(StrEnum):
    """Operational status labels for workflow health."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
