"""State definitions for adaptive intelligence."""

from __future__ import annotations

from enum import StrEnum


class AdaptiveState(StrEnum):
    CREATED = "created"
    QUEUED = "queued"
    REVIEWING = "reviewing"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    APPLIED = "applied"
    EXPIRED = "expired"
