"""Provider permission model."""

from __future__ import annotations

from enum import StrEnum


class ProviderPermission(StrEnum):
    """Permissions that may be required by provider adapters."""

    INTERNET = "internet"
    LOCAL_MODEL = "local_model"
    API_KEY = "api_key"
    STREAMING = "streaming"
    FILE_UPLOAD = "file_upload"


class ProviderPermissionSet:
    """Immutable provider permission collection."""

    def __init__(self, permissions: tuple[ProviderPermission, ...] = ()) -> None:
        self._permissions = frozenset(permissions)

    def has(self, permission: ProviderPermission) -> bool:
        """Return whether a permission is present."""
        return permission in self._permissions

    def require(self, permission: ProviderPermission) -> None:
        """Raise if a permission is absent."""
        if permission not in self._permissions:
            raise PermissionError(f"Provider permission required: {permission.value}")
