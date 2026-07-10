"""Base class for all JARVIS OS plugins."""

from __future__ import annotations

from abc import ABC

from plugins.plugin_context import PluginContext
from plugins.plugin_manifest import PluginManifest
from plugins.plugin_state import PluginLifecycleState


class BasePlugin(ABC):
    """Base class every plugin must inherit from."""

    def __init__(self, context: PluginContext) -> None:
        self.context = context
        self.manifest: PluginManifest = context.manifest
        self.state = PluginLifecycleState.LOADED

    @property
    def plugin_id(self) -> str:
        """Return the plugin unique ID."""
        return self.manifest.plugin_id

    def on_load(self) -> None:
        """Hook called after plugin object creation."""

    def on_initialize(self) -> None:
        """Hook called before a plugin is enabled."""

    def on_enable(self) -> None:
        """Hook called when a plugin is enabled."""

    def on_disable(self) -> None:
        """Hook called when a plugin is disabled."""

    def on_unload(self) -> None:
        """Hook called when a plugin is unloaded."""

    def on_shutdown(self) -> None:
        """Hook called during application shutdown."""
