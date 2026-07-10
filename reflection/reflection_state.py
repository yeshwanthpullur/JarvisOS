"""State definitions for reflection sessions."""

from __future__ import annotations

from enum import StrEnum


class ReflectionState(StrEnum):
    CREATED = "created"
    ANALYZING = "analyzing"
    REPORTED = "reported"
    LEARNING = "learning"
    COMPLETE = "complete"
    FAILED = "failed"
