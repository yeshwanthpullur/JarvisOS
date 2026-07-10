"""Task priority values for queue ordering."""

from __future__ import annotations

from enum import IntEnum


class TaskPriority(IntEnum):
    """Priority values where a lower number means higher urgency."""

    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3

