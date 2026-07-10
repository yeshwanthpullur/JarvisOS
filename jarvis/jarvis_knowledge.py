"""Knowledge integration adapter for Executive JARVIS."""

from __future__ import annotations

from typing import Any


class JarvisKnowledge:
    """Coordinates with Knowledge Engine and Obsidian Brain interfaces."""

    initialized = True

    def __init__(self, knowledge_manager: Any | None = None, brain_manager: Any | None = None) -> None:
        self.knowledge_manager = knowledge_manager
        self.brain_manager = brain_manager

    def is_available(self) -> bool:
        """Return whether knowledge is attached."""
        return self.knowledge_manager is not None

    def statistics(self) -> dict[str, object]:
        """Return knowledge statistics if available."""
        if self.knowledge_manager is None or not hasattr(self.knowledge_manager, "statistics"):
            return {}
        stats = self.knowledge_manager.statistics()
        return {"total_documents": getattr(stats, "total_documents", 0)}

