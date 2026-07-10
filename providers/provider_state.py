"""Provider lifecycle state definitions."""

from __future__ import annotations

from enum import StrEnum


class ProviderLifecycleState(StrEnum):
    """Provider lifecycle state."""

    DISCOVERED = "discovered"
    REGISTERED = "registered"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNHEALTHY = "unhealthy"
    REMOVED = "removed"
