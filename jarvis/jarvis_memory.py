"""Memory integration adapter for Executive JARVIS."""

from __future__ import annotations

from typing import Any


class JarvisMemory:
    """Coordinates with the existing Memory Engine through its public manager."""

    initialized = True

    def __init__(self, memory_manager: Any | None = None) -> None:
        self.memory_manager = memory_manager

    def is_available(self) -> bool:
        """Return whether a memory manager is attached."""
        return self.memory_manager is not None

    def statistics(self) -> dict[str, object]:
        """Return memory statistics if available."""
        if self.memory_manager is None or not hasattr(self.memory_manager, "statistics"):
            return {}
        stats = self.memory_manager.statistics()
        return {"total_memories": getattr(stats, "total_memories", 0)}

