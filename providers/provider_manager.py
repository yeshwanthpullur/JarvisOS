"""High-level AI Provider Router manager."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from config.schema import AppSettings, ProvidersConfig
from providers.provider_factory import ProviderFactory
from providers.provider_loader import ProviderLoader
from providers.provider_registry import ProviderRegistry
from providers.provider_router import ProviderRouter


@dataclass(frozen=True, slots=True)
class ProviderRouterStatistics:
    """Startup and operational provider statistics."""

    registered_providers: int
    enabled_providers: int
    healthy_providers: int


class ProviderManager:
    """Coordinates provider discovery, registration, health, and routing."""

    def __init__(
        self,
        config: ProvidersConfig,
        settings: AppSettings | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.registry = ProviderRegistry(logger=self._logger)
        self.loader = ProviderLoader(config, logger=self._logger)
        self.factory = ProviderFactory(settings=settings, logger=self._logger)
        self.router = ProviderRouter(logger=self._logger)
        self.initialized = False

    def initialize(self) -> ProviderRouterStatistics:
        """Discover, create, initialize, and route provider adapters."""
        for config in self.loader.discover():
            self.registry.register_config(config)
            provider = self.factory.create(config)
            provider.initialize()
            record = self.registry.attach_provider(provider)
            if config.enabled:
                self.registry.enable(config.provider_id)
                self.router.register_provider(provider)
            else:
                self.registry.disable(config.provider_id)
            record.health = provider.health_check()
        self.initialized = True
        self._logger.info("provider_router_initialized registered=%s enabled=%s", self.statistics().registered_providers, self.statistics().enabled_providers)
        return self.statistics()

    def enable_provider(self, provider_id: str) -> None:
        """Enable a provider and make it routable."""
        record = self.registry.require(provider_id)
        if record.provider is None:
            record.provider = self.factory.create(record.config)
            record.provider.initialize()
        self.registry.enable(provider_id)
        self.router.register_provider(record.provider)

    def disable_provider(self, provider_id: str) -> None:
        """Disable a provider and remove it from routing."""
        self.registry.disable(provider_id)
        self.router.unregister_provider(provider_id)

    def reload_provider(self, provider_id: str) -> None:
        """Reload a provider adapter from its config."""
        self.disable_provider(provider_id)
        self.enable_provider(provider_id)

    def remove_provider(self, provider_id: str) -> None:
        """Remove a provider from routing."""
        self.router.unregister_provider(provider_id)
        self.registry.remove(provider_id)

    def health_check(self) -> dict[str, object]:
        """Run no-network health checks for all providers."""
        results: dict[str, object] = {}
        for record in self.registry.all():
            if record.provider is not None:
                record.health = record.provider.health_check()
                results[record.config.provider_id] = record.health
        return results

    def statistics(self) -> ProviderRouterStatistics:
        """Return provider router statistics."""
        records = self.registry.all()
        enabled = self.registry.enabled_providers()
        return ProviderRouterStatistics(
            registered_providers=len(records),
            enabled_providers=len(enabled),
            healthy_providers=len(enabled),
        )

    def shutdown(self) -> None:
        """Shutdown all provider adapters."""
        for record in self.registry.all():
            if record.provider is not None:
                record.provider.shutdown()
