"""Conversation memory adapter."""

from __future__ import annotations

from typing import Any


class ConversationMemory:
    """References the existing Memory Engine without duplicating storage."""

    def __init__(self, memory_manager: Any | None = None) -> None:
        self.memory_manager = memory_manager
        self.initialized = True

    def is_available(self) -> bool:
        """Return whether memory is attached."""
        return self.memory_manager is not None

