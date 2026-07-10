"""Runtime context passed to plugin instances."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from config.schema import AppSettings
from plugins.plugin_config import PluginConfig
from plugins.plugin_events import PluginEventBus
from plugins.plugin_manifest import PluginManifest
from plugins.plugin_permissions import PermissionSet, PluginPermission


@dataclass(frozen=True, slots=True)
class PluginContext:
    """Safe runtime context exposed to plugins."""

    manifest: PluginManifest
    settings: AppSettings | None
    plugin_dir: Path
    config: PluginConfig
    permissions: PermissionSet
    events: PluginEventBus
    logger: logging.Logger

    def require_permission(self, permission: PluginPermission) -> None:
        """Require a permission before a plugin performs a capability."""
        self.permissions.require(permission)
