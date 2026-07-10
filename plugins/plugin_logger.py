"""Plugin-specific logging helpers."""

from __future__ import annotations

import logging


class PluginLoggerFactory:
    """Creates namespaced loggers for plugins."""

    def get_logger(self, plugin_id: str) -> logging.Logger:
        """Return a logger for a plugin."""
        return logging.getLogger(f"plugins.{plugin_id}")
