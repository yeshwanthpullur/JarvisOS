"""Permission model for JARVIS OS plugins."""

from __future__ import annotations

from enum import StrEnum


class PluginPermission(StrEnum):
    """Supported plugin permission names."""

    FILESYSTEM = "filesystem"
    INTERNET = "internet"
    CAMERA = "camera"
    DESKTOP = "desktop"
    CLIPBOARD = "clipboard"
    DOWNLOADS = "downloads"
    NOTIFICATIONS = "notifications"
    MICROPHONE = "microphone"
    SYSTEM = "system"
    BROWSER = "browser"
    MOBILE = "mobile"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    TASKS = "tasks"


class PermissionSet:
    """Immutable plugin permission collection."""

    def __init__(self, permissions: tuple[PluginPermission, ...] = ()) -> None:
        self._permissions = frozenset(permissions)

    @classmethod
    def from_strings(cls, values: tuple[str, ...]) -> "PermissionSet":
        """Create permissions from string values."""
        return cls(tuple(PluginPermission(value) for value in values))

    def has(self, permission: PluginPermission) -> bool:
        """Return whether a permission is granted."""
        return permission in self._permissions

    def require(self, permission: PluginPermission) -> None:
        """Raise if a permission is not granted."""
        if not self.has(permission):
            raise PermissionError(f"Plugin permission required: {permission.value}")

    def as_tuple(self) -> tuple[PluginPermission, ...]:
        """Return permissions as a tuple."""
        return tuple(sorted(self._permissions, key=lambda item: item.value))
