"""Agent cache interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AgentCache(ABC):
    """Base cache interface for future cache implementations."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Return a cached value."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Store a cached value."""


class RuntimeCache(AgentCache):
    """Runtime cache interface."""


class ContextCache(AgentCache):
    """Context cache interface."""


class CheckpointCache(AgentCache):
    """Checkpoint cache interface."""


class ConfigurationCache(AgentCache):
    """Configuration cache interface."""


class SessionCache(AgentCache):
    """Session cache interface."""


class CapabilityCache(AgentCache):
    """Capability cache interface."""


class PermissionCache(AgentCache):
    """Permission cache interface."""
