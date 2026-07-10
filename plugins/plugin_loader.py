"""Plugin discovery and dynamic loading."""

from __future__ import annotations

import importlib.util
import logging
from pathlib import Path

from config.schema import AppSettings
from plugins.plugin_base import BasePlugin
from plugins.plugin_config import PluginConfig
from plugins.plugin_context import PluginContext
from plugins.plugin_events import PluginEventBus
from plugins.plugin_logger import PluginLoggerFactory
from plugins.plugin_manifest import MANIFEST_FILENAME, PluginManifest
from plugins.plugin_permissions import PermissionSet


class PluginLoader:
    """Discovers plugin manifests and loads plugin classes."""

    def __init__(
        self,
        plugin_dir: Path,
        settings: AppSettings | None = None,
        event_bus: PluginEventBus | None = None,
        logger_factory: PluginLoggerFactory | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._plugin_dir = plugin_dir
        self._settings = settings
        self._events = event_bus or PluginEventBus()
        self._logger_factory = logger_factory or PluginLoggerFactory()
        self._logger = logger or logging.getLogger(__name__)

    def discover(self) -> tuple[PluginManifest, ...]:
        """Discover plugin manifests from the configured plugins directory."""
        self._plugin_dir.mkdir(parents=True, exist_ok=True)
        manifests: list[PluginManifest] = []
        for manifest_path in sorted(self._plugin_dir.rglob(MANIFEST_FILENAME)):
            manifest = PluginManifest.from_file(manifest_path)
            manifests.append(manifest)
            self._logger.info("plugin_discovered plugin_id=%s path=%s", manifest.plugin_id, manifest_path)
        return tuple(manifests)

    def load(self, manifest: PluginManifest) -> BasePlugin:
        """Load a plugin instance from its entry point."""
        if manifest.path is None:
            raise ValueError("Cannot load a plugin without a manifest path.")
        module_name, class_name = manifest.entry_point.split(":", 1)
        module_path = manifest.path / f"{module_name.replace('.', '/')}.py"
        if not module_path.exists():
            raise FileNotFoundError(f"Plugin module not found: {module_path}")

        import_name = f"jarvis_plugin_{manifest.plugin_id.replace('.', '_').replace('-', '_')}"
        spec = importlib.util.spec_from_file_location(import_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load plugin module: {module_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        plugin_class = getattr(module, class_name)
        if not issubclass(plugin_class, BasePlugin):
            raise TypeError("Plugin class must inherit from BasePlugin.")

        context = PluginContext(
            manifest=manifest,
            settings=self._settings,
            plugin_dir=manifest.path,
            config=PluginConfig(dict(manifest.configuration)),
            permissions=PermissionSet(manifest.permissions),
            events=self._events,
            logger=self._logger_factory.get_logger(manifest.plugin_id),
        )
        instance = plugin_class(context)
        self._logger.info("plugin_loaded plugin_id=%s", manifest.plugin_id)
        return instance
