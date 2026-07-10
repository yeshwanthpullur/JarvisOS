"""Plugin integration adapter for Executive JARVIS."""

from __future__ import annotations

from typing import Any


class JarvisPlugins:
    """Coordinates with the Plugin Framework."""

    initialized = True

    def __init__(self, plugin_manager: Any | None = None) -> None:
        self.plugin_manager = plugin_manager

    def is_available(self) -> bool:
        """Return whether plugin manager is attached."""
        return self.plugin_manager is not None

    def statistics(self) -> dict[str, object]:
        """Return plugin statistics if available."""
        if self.plugin_manager is None or not hasattr(self.plugin_manager, "statistics"):
            return {}
        stats = self.plugin_manager.statistics()
        return {"loaded_plugins": getattr(stats, "loaded_plugins", 0)}

