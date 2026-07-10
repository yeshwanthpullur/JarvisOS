"""High-level Plugin Framework manager."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from config.schema import AppSettings
from plugins.plugin_events import PluginEvent, PluginEventBus
from plugins.plugin_installer import PluginInstaller
from plugins.plugin_loader import PluginLoader
from plugins.plugin_registry import PluginRecord, PluginRegistry
from plugins.plugin_state import PluginLifecycleState
from plugins.plugin_uninstaller import PluginUninstaller
from plugins.plugin_validator import PluginValidator


@dataclass(frozen=True, slots=True)
class PluginFrameworkStatistics:
    """Operational plugin framework statistics."""

    discovered_plugins: int
    valid_plugins: int
    loaded_plugins: int
    enabled_plugins: int
    invalid_plugins: int


class PluginManager:
    """Coordinates plugin discovery, validation, loading, and lifecycle."""

    def __init__(
        self,
        plugin_dir: Path,
        settings: AppSettings | None = None,
        auto_enable: bool = True,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._events = PluginEventBus(logger=self._logger)
        self.registry = PluginRegistry(logger=self._logger)
        self.validator = PluginValidator()
        self.loader = PluginLoader(
            plugin_dir=plugin_dir,
            settings=settings,
            event_bus=self._events,
            logger=self._logger,
        )
        self.installer = PluginInstaller(plugin_dir, logger=self._logger)
        self.uninstaller = PluginUninstaller(plugin_dir, logger=self._logger)
        self._auto_enable = auto_enable
        self.initialized = False

    def initialize(self) -> PluginFrameworkStatistics:
        """Initialize the plugin framework and auto-load valid plugins."""
        self.discover_plugins()
        self.validate_plugins()
        self.load_plugins()
        for record in self.registry.all():
            if record.instance is not None:
                self.initialize_plugin(record.manifest.plugin_id)
                if self._auto_enable:
                    self.enable_plugin(record.manifest.plugin_id)
        self.initialized = True
        self._logger.info("plugin_framework_initialized loaded=%s", self.registry.loaded_count())
        return self.statistics()

    def discover_plugins(self) -> tuple[PluginRecord, ...]:
        """Discover plugin manifests and register them."""
        records = tuple(
            self.registry.register_manifest(manifest)
            for manifest in self.loader.discover()
        )
        for record in records:
            self._publish(record.manifest.plugin_id, "discover")
        return records

    def validate_plugins(self) -> tuple[PluginRecord, ...]:
        """Validate all registered plugins."""
        available_ids = self.registry.plugin_ids()
        records: list[PluginRecord] = []
        for record in self.registry.all():
            result = self.validator.validate_manifest(record.manifest, available_ids)
            if result.valid:
                self.registry.set_state(
                    record.manifest.plugin_id,
                    PluginLifecycleState.VALIDATED,
                )
            else:
                self.registry.set_state(record.manifest.plugin_id, PluginLifecycleState.INVALID)
                self.registry.set_errors(record.manifest.plugin_id, result.errors)
            self._publish(record.manifest.plugin_id, "validate")
            records.append(self.registry.require(record.manifest.plugin_id))
        return tuple(records)

    def load_plugins(self) -> tuple[PluginRecord, ...]:
        """Load all valid plugins whose dependencies are available."""
        loaded: list[PluginRecord] = []
        remaining = [
            record
            for record in self.registry.all()
            if record.state is PluginLifecycleState.VALIDATED
        ]
        while remaining:
            progressed = False
            for record in tuple(remaining):
                if self._dependencies_loaded(record):
                    self.load_plugin(record.manifest.plugin_id)
                    loaded.append(self.registry.require(record.manifest.plugin_id))
                    remaining.remove(record)
                    progressed = True
            if not progressed:
                for record in remaining:
                    self.registry.set_state(record.manifest.plugin_id, PluginLifecycleState.INVALID)
                    self.registry.set_errors(
                        record.manifest.plugin_id,
                        ("Dependency cycle or unloaded dependency detected.",),
                    )
                break
        return tuple(loaded)

    def load_plugin(self, plugin_id: str) -> PluginRecord:
        """Load a single plugin and run its load hook."""
        record = self.registry.require(plugin_id)
        instance = self.loader.load(record.manifest)
        self.registry.set_instance(plugin_id, instance)
        instance.on_load()
        self.registry.set_state(plugin_id, PluginLifecycleState.LOADED)
        self._publish(plugin_id, "load")
        return self.registry.require(plugin_id)

    def initialize_plugin(self, plugin_id: str) -> PluginRecord:
        """Initialize a loaded plugin."""
        record = self.registry.require(plugin_id)
        if record.instance is None:
            raise RuntimeError(f"Plugin is not loaded: {plugin_id}")
        record.instance.on_initialize()
        self.registry.set_state(plugin_id, PluginLifecycleState.INITIALIZED)
        self._publish(plugin_id, "initialize")
        return self.registry.require(plugin_id)

    def enable_plugin(self, plugin_id: str) -> PluginRecord:
        """Enable an initialized or disabled plugin."""
        record = self.registry.require(plugin_id)
        if record.instance is None:
            raise RuntimeError(f"Plugin is not loaded: {plugin_id}")
        record.instance.on_enable()
        self.registry.set_state(plugin_id, PluginLifecycleState.ENABLED)
        self._publish(plugin_id, "enable")
        return self.registry.require(plugin_id)

    def disable_plugin(self, plugin_id: str) -> PluginRecord:
        """Disable an enabled plugin."""
        record = self.registry.require(plugin_id)
        if record.instance is None:
            raise RuntimeError(f"Plugin is not loaded: {plugin_id}")
        record.instance.on_disable()
        self.registry.set_state(plugin_id, PluginLifecycleState.DISABLED)
        self._publish(plugin_id, "disable")
        return self.registry.require(plugin_id)

    def reload_plugin(self, plugin_id: str) -> PluginRecord:
        """Reload a plugin from disk."""
        self.unload_plugin(plugin_id)
        self.load_plugin(plugin_id)
        self.initialize_plugin(plugin_id)
        self.enable_plugin(plugin_id)
        self._publish(plugin_id, "reload")
        return self.registry.require(plugin_id)

    def unload_plugin(self, plugin_id: str) -> PluginRecord:
        """Unload a plugin instance."""
        record = self.registry.require(plugin_id)
        if record.instance is not None:
            if record.state is PluginLifecycleState.ENABLED:
                record.instance.on_disable()
            record.instance.on_unload()
            record.instance = None
        self.registry.set_state(plugin_id, PluginLifecycleState.UNLOADED)
        self._publish(plugin_id, "unload")
        return self.registry.require(plugin_id)

    def remove_plugin(self, plugin_id: str) -> PluginRecord:
        """Mark a plugin removed after unload. Physical deletion is future behavior."""
        self.unload_plugin(plugin_id)
        self.registry.set_state(plugin_id, PluginLifecycleState.REMOVED)
        self._publish(plugin_id, "remove")
        return self.registry.require(plugin_id)

    def shutdown(self) -> None:
        """Run shutdown hooks for loaded plugins."""
        for record in self.registry.all():
            if record.instance is not None:
                record.instance.on_shutdown()
                self._publish(record.manifest.plugin_id, "shutdown")

    def statistics(self) -> PluginFrameworkStatistics:
        """Return plugin framework statistics."""
        records = self.registry.all()
        return PluginFrameworkStatistics(
            discovered_plugins=len(records),
            valid_plugins=sum(
                1
                for record in records
                if record.state
                in {
                    PluginLifecycleState.VALIDATED,
                    PluginLifecycleState.LOADED,
                    PluginLifecycleState.INITIALIZED,
                    PluginLifecycleState.ENABLED,
                    PluginLifecycleState.DISABLED,
                }
            ),
            loaded_plugins=self.registry.loaded_count(),
            enabled_plugins=sum(
                1 for record in records if record.state is PluginLifecycleState.ENABLED
            ),
            invalid_plugins=sum(
                1 for record in records if record.state is PluginLifecycleState.INVALID
            ),
        )

    def _dependencies_loaded(self, record: PluginRecord) -> bool:
        for dependency in record.manifest.dependencies:
            dependency_record = self.registry.get(dependency)
            if dependency_record is None or dependency_record.instance is None:
                return False
        return True

    def _publish(self, plugin_id: str, event_type: str) -> None:
        self._events.publish(PluginEvent(plugin_id=plugin_id, event_type=event_type))
