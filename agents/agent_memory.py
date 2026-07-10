"""Agent memory integration interface."""

from __future__ import annotations

from typing import Any


class AgentMemoryInterface:
    """Reference wrapper for MemoryManager without duplicating memory logic."""

    def __init__(self, memory_manager: Any | None = None) -> None:
        self.memory_manager = memory_manager

    def is_available(self) -> bool:
        """Return whether memory is attached."""
        return self.memory_manager is not None
