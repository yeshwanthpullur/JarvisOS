"""Plugin lifecycle state definitions."""

from __future__ import annotations

from enum import StrEnum


class PluginLifecycleState(StrEnum):
    """Lifecycle states for plugin management."""

    DISCOVERED = "discovered"
    VALIDATED = "validated"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLOADED = "unloaded"
    REMOVED = "removed"
    INVALID = "invalid"


class PluginLifecycleAction(StrEnum):
    """Lifecycle actions supported by the framework."""

    DISCOVER = "discover"
    VALIDATE = "validate"
    LOAD = "load"
    INITIALIZE = "initialize"
    ENABLE = "enable"
    DISABLE = "disable"
    RELOAD = "reload"
    UNLOAD = "unload"
    REMOVE = "remove"
