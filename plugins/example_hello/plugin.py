"""Example JARVIS OS plugin."""

from __future__ import annotations

from plugins import BasePlugin


class HelloPlugin(BasePlugin):
    """Minimal example plugin used by tests and startup discovery."""

    def on_load(self) -> None:
        """Log and print a successful load message."""
        message = str(self.context.config.get("message", "Plugin Loaded Successfully"))
        print(message)
        self.context.logger.info("hello_plugin_loaded message=%s", message)
