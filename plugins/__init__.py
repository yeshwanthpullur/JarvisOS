"""Plugin package for optional integrations and extension modules."""
"""Plugin Framework for JARVIS OS extensions."""

from plugins.plugin_base import BasePlugin
from plugins.plugin_config import PluginConfig
from plugins.plugin_context import PluginContext
from plugins.plugin_events import PluginEvent, PluginEventBus
from plugins.plugin_loader import PluginLoader
from plugins.plugin_manager import PluginFrameworkStatistics, PluginManager
from plugins.plugin_manifest import PluginManifest
from plugins.plugin_permissions import PermissionSet, PluginPermission
from plugins.plugin_registry import PluginRecord, PluginRegistry
from plugins.plugin_state import PluginLifecycleAction, PluginLifecycleState
from plugins.plugin_validator import PluginValidationResult, PluginValidator

__all__ = [
    "BasePlugin",
    "PermissionSet",
    "PluginConfig",
    "PluginContext",
    "PluginEvent",
    "PluginEventBus",
    "PluginFrameworkStatistics",
    "PluginLifecycleAction",
    "PluginLifecycleState",
    "PluginLoader",
    "PluginManager",
    "PluginManifest",
    "PluginPermission",
    "PluginRecord",
    "PluginRegistry",
    "PluginValidationResult",
    "PluginValidator",
]
