"""Runtime context for provider adapters."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from config.schema import AppSettings
from providers.provider_config import ProviderConfig
from providers.provider_permissions import ProviderPermission, ProviderPermissionSet


@dataclass(frozen=True, slots=True)
class ProviderContext:
    """Safe context passed into provider adapters."""

    config: ProviderConfig
    settings: AppSettings | None
    permissions: ProviderPermissionSet
    logger: logging.Logger

    def require_permission(self, permission: ProviderPermission) -> None:
        """Require a provider permission."""
        self.permissions.require(permission)
