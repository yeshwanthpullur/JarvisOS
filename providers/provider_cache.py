"""Provider cache interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ResponseCache(ABC):
    """Future response cache contract."""

    @abstractmethod
    def get(self, key: str) -> Any | None:
        """Return a cached response."""

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Store a cached response."""


class ModelCache(ABC):
    """Future model cache contract."""

    @abstractmethod
    def get_models(self, provider_id: str) -> Any | None:
        """Return cached model data."""

    @abstractmethod
    def set_models(self, provider_id: str, models: Any) -> None:
        """Store cached model data."""


class CapabilityCache(ABC):
    """Future capability cache contract."""

    @abstractmethod
    def get_capabilities(self, provider_id: str) -> Any | None:
        """Return cached capability data."""

    @abstractmethod
    def set_capabilities(self, provider_id: str, capabilities: Any) -> None:
        """Store cached capability data."""
