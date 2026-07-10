"""In-memory plugin registry."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from plugins.plugin_base import BasePlugin
from plugins.plugin_manifest import PluginManifest
from plugins.plugin_state import PluginLifecycleState


@dataclass(slots=True)
class PluginRecord:
    """Registry record for one plugin."""

    manifest: PluginManifest
    state: PluginLifecycleState
    instance: BasePlugin | None = None
    errors: tuple[str, ...] = ()


class PluginRegistry:
    """Tracks discovered plugin manifests and loaded plugin instances."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._records: dict[str, PluginRecord] = {}
        self._logger = logger or logging.getLogger(__name__)

    def register_manifest(self, manifest: PluginManifest) -> PluginRecord:
        """Register or update a plugin manifest."""
        record = PluginRecord(
            manifest=manifest,
            state=PluginLifecycleState.DISCOVERED,
        )
        self._records[manifest.plugin_id] = record
        self._logger.info("plugin_manifest_registered plugin_id=%s", manifest.plugin_id)
        return record

    def set_instance(self, plugin_id: str, instance: BasePlugin) -> None:
        """Attach a loaded plugin instance to a record."""
        record = self.require(plugin_id)
        record.instance = instance
        record.state = instance.state

    def set_state(self, plugin_id: str, state: PluginLifecycleState) -> None:
        """Update a plugin lifecycle state."""
        record = self.require(plugin_id)
        record.state = state
        if record.instance is not None:
            record.instance.state = state
        self._logger.info("plugin_state_changed plugin_id=%s state=%s", plugin_id, state.value)

    def set_errors(self, plugin_id: str, errors: tuple[str, ...]) -> None:
        """Store validation or loading errors."""
        record = self.require(plugin_id)
        record.errors = errors
        self._logger.warning("plugin_errors plugin_id=%s errors=%s", plugin_id, errors)

    def get(self, plugin_id: str) -> PluginRecord | None:
        """Return a plugin record by ID."""
        return self._records.get(plugin_id)

    def require(self, plugin_id: str) -> PluginRecord:
        """Return a plugin record or raise."""
        record = self.get(plugin_id)
        if record is None:
            raise KeyError(f"Plugin not registered: {plugin_id}")
        return record

    def all(self) -> tuple[PluginRecord, ...]:
        """Return all plugin records."""
        return tuple(self._records.values())

    def plugin_ids(self) -> tuple[str, ...]:
        """Return all registered plugin IDs."""
        return tuple(self._records.keys())

    def loaded_count(self) -> int:
        """Return the number of loaded or enabled plugin instances."""
        return sum(1 for record in self._records.values() if record.instance is not None)
