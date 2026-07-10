"""Provider registry for AI backend interfaces."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from providers.base_provider import BaseProvider
from providers.provider_config import ProviderConfig
from providers.provider_health import ProviderHealth
from providers.provider_metrics import ProviderMetrics
from providers.provider_state import ProviderLifecycleState


@dataclass(slots=True)
class ProviderRecord:
    """Registry record for one provider."""

    config: ProviderConfig
    provider: BaseProvider | None = None
    state: ProviderLifecycleState = ProviderLifecycleState.DISCOVERED
    health: ProviderHealth | None = None
    metrics: ProviderMetrics | None = None


class ProviderRegistry:
    """Tracks provider configurations and live provider adapters."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._records: dict[str, ProviderRecord] = {}
        self._logger = logger or logging.getLogger(__name__)

    def register_config(self, config: ProviderConfig) -> ProviderRecord:
        """Register provider configuration."""
        record = ProviderRecord(config=config)
        self._records[config.provider_id] = record
        self._logger.info("provider_registered provider_id=%s kind=%s", config.provider_id, config.kind.value)
        return record

    def attach_provider(self, provider: BaseProvider) -> ProviderRecord:
        """Attach a provider adapter to a record."""
        record = self.require(provider.provider_id)
        record.provider = provider
        record.health = provider.health
        record.metrics = provider.metrics
        record.state = ProviderLifecycleState.ENABLED if provider.enabled else ProviderLifecycleState.DISABLED
        return record

    def enable(self, provider_id: str) -> None:
        """Enable a provider."""
        record = self.require(provider_id)
        record.state = ProviderLifecycleState.ENABLED
        if record.provider is not None:
            record.provider.enabled = True

    def disable(self, provider_id: str) -> None:
        """Disable a provider."""
        record = self.require(provider_id)
        record.state = ProviderLifecycleState.DISABLED
        if record.provider is not None:
            record.provider.enabled = False

    def remove(self, provider_id: str) -> None:
        """Mark a provider removed."""
        record = self.require(provider_id)
        record.state = ProviderLifecycleState.REMOVED
        record.provider = None

    def get(self, provider_id: str) -> ProviderRecord | None:
        """Return provider record if present."""
        return self._records.get(provider_id)

    def require(self, provider_id: str) -> ProviderRecord:
        """Return provider record or raise."""
        record = self.get(provider_id)
        if record is None:
            raise KeyError(f"Provider not registered: {provider_id}")
        return record

    def all(self) -> tuple[ProviderRecord, ...]:
        """Return all provider records."""
        return tuple(self._records.values())

    def enabled_providers(self) -> tuple[BaseProvider, ...]:
        """Return enabled provider adapters."""
        return tuple(
            record.provider
            for record in self._records.values()
            if record.provider is not None and record.state is ProviderLifecycleState.ENABLED
        )

    def provider_ids(self) -> tuple[str, ...]:
        """Return registered provider IDs."""
        return tuple(self._records)
