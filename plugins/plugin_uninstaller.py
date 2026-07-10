"""Plugin uninstallation interfaces."""

from __future__ import annotations

import logging
from pathlib import Path


class PluginUninstaller:
    """Placeholder uninstaller for future removable plugins."""

    def __init__(self, plugin_dir: Path, logger: logging.Logger | None = None) -> None:
        self._plugin_dir = plugin_dir
        self._logger = logger or logging.getLogger(__name__)

    def can_remove(self, plugin_id: str) -> bool:
        """Return whether a plugin directory exists for removal."""
        if not self._plugin_dir.exists():
            return False
        return any(
            path.is_dir() and path.name == plugin_id
            for path in self._plugin_dir.iterdir()
        )

    def remove(self, plugin_id: str) -> None:
        """Declare removal as future behavior."""
        if not self.can_remove(plugin_id):
            raise FileNotFoundError(f"Plugin not found: {plugin_id}")
        raise NotImplementedError("Plugin removal is not implemented yet.")
