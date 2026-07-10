"""Agent permission metadata."""

from __future__ import annotations

from enum import StrEnum


class AgentPermission(StrEnum):
    """Declarative permissions an agent may request."""

    FILESYSTEM = "filesystem"
    INTERNET = "internet"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    TASKS = "tasks"
    PROVIDERS = "providers"
    PLUGINS = "plugins"
    CONFIGURATION = "configuration"
    DESKTOP = "desktop"
    CAMERA = "camera"
    MICROPHONE = "microphone"
    NOTIFICATIONS = "notifications"
    CLIPBOARD = "clipboard"
    DOWNLOADS = "downloads"
    DOCUMENTS = "documents"
    SYSTEM = "system"
    MOBILE = "mobile"
    VOICE = "voice"
    VISION = "vision"
    FUTURE_EXTENSIONS = "future_extensions"


class AgentPermissionSet:
    """Immutable set of agent permissions."""

    def __init__(self, permissions: tuple[AgentPermission, ...] = ()) -> None:
        self._permissions = frozenset(permissions)

    def has(self, permission: AgentPermission) -> bool:
        """Return whether the permission exists."""
        return permission in self._permissions

    def require(self, permission: AgentPermission) -> None:
        """Raise when a permission is absent."""
        if permission not in self._permissions:
            raise PermissionError(f"Agent permission required: {permission.value}")

    def as_tuple(self) -> tuple[AgentPermission, ...]:
        """Return sorted permissions."""
        return tuple(sorted(self._permissions, key=lambda item: item.value))
