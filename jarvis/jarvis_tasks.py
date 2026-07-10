"""Task integration adapter for Executive JARVIS."""

from __future__ import annotations

from typing import Any


class JarvisTasks:
    """Coordinates with the existing Task Engine."""

    initialized = True

    def __init__(self, task_manager: Any | None = None) -> None:
        self.task_manager = task_manager

    def is_available(self) -> bool:
        """Return whether task manager is attached."""
        return self.task_manager is not None

    def statistics(self) -> dict[str, object]:
        """Return task statistics if available."""
        if self.task_manager is None or not hasattr(self.task_manager, "statistics"):
            return {}
        stats = self.task_manager.statistics()
        return {"total_tasks": getattr(stats, "total_tasks", 0)}

