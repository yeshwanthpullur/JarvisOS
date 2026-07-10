"""Plugin installation interfaces."""

from __future__ import annotations

import logging
from pathlib import Path


class PluginInstaller:
    """Placeholder installer for future plugin package installation."""

    def __init__(self, plugin_dir: Path, logger: logging.Logger | None = None) -> None:
        self._plugin_dir = plugin_dir
        self._logger = logger or logging.getLogger(__name__)

    def can_install_from_directory(self, source_dir: Path) -> bool:
        """Return whether a directory appears to contain a plugin manifest."""
        return source_dir.is_dir() and (source_dir / "plugin.json").exists()

    def install_from_directory(self, source_dir: Path) -> None:
        """Declare installation as future behavior."""
        if not self.can_install_from_directory(source_dir):
            raise ValueError(f"Invalid plugin source directory: {source_dir}")
        raise NotImplementedError("Plugin installation is not implemented yet.")
