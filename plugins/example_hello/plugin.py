"""Example JARVIS OS plugin."""

from __future__ import annotations

from plugins import BasePlugin


class HelloPlugin(BasePlugin):
    """Minimal example plugin used by tests and startup discovery."""

    def on_load(self) -> None:
        """Record a successful load without writing into the chat console."""
        message = str(self.context.config.get("message", "Plugin Loaded Successfully"))
        self.context.logger.info("hello_plugin_loaded message=%s", message)
