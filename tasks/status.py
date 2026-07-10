"""Task status values for the JARVIS OS Task Engine."""

from __future__ import annotations

from enum import StrEnum


class TaskStatus(StrEnum):
    """Supported lifecycle states for a task."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


TERMINAL_STATUSES = frozenset(
    {
        TaskStatus.COMPLETED,
        TaskStatus.FAILED,
        TaskStatus.CANCELLED,
    }
)

