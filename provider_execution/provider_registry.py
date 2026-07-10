"""Execution-time provider registry."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from providers.provider_types import ProviderCapability
from provider_execution.provider_capabilities import ProviderCapabilities
from provider_execution.provider_health import ProviderExecutionHealth, ProviderHealthState
from provider_execution.provider_metrics import ProviderExecutionMetrics


@dataclass(slots=True)
class ProviderExecutionRecord:
    """Registry record used by the provider execution layer."""

    provider_id: str
    capabilities: ProviderCapabilities = field(default_factory=ProviderCapabilities)
    health: ProviderExecutionHealth = field(default_factory=ProviderExecutionHealth)
    metrics: ProviderExecutionMetrics = field(default_factory=ProviderExecutionMetrics)
    enabled: bool = True
    priority: int = 5
    version: str = "0.1"
    configuration: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderExecutionRegistry:
    """Single source of truth for provider execution metadata."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._records: dict[str, ProviderExecutionRecord] = {}
        self.initialized = True
        self._logger = logger or logging.getLogger(__name__)

    def register(self, record: ProviderExecutionRecord) -> None:
        """Register or replace provider execution metadata."""
        self._records[record.provider_id] = record
        self._logger.info("provider_execution_registered provider_id=%s", record.provider_id)

    def unregister(self, provider_id: str) -> None:
        """Remove provider execution metadata."""
        self._records.pop(provider_id, None)
        self._logger.info("provider_execution_unregistered provider_id=%s", provider_id)

    def enable(self, provider_id: str) -> None:
        """Enable an execution provider."""
        self.require(provider_id).enabled = True

    def disable(self, provider_id: str) -> None:
        """Disable an execution provider."""
        record = self.require(provider_id)
        record.enabled = False
        record.health.state = ProviderHealthState.DISABLED

    def lookup(self, provider_id: str) -> ProviderExecutionRecord | None:
        """Return a record by provider ID."""
        return self._records.get(provider_id)

    def require(self, provider_id: str) -> ProviderExecutionRecord:
        """Return a record or raise a clear error."""
        record = self.lookup(provider_id)
        if record is None:
            raise KeyError(f"Provider execution record not found: {provider_id}")
        return record

    def discover(self) -> tuple[ProviderExecutionRecord, ...]:
        """Return all discovered execution records."""
        return tuple(self._records.values())

    def validate(self, provider_id: str) -> bool:
        """Validate that a provider record has required metadata."""
        record = self.lookup(provider_id)
        return record is not None and bool(record.provider_id)

    def capability_lookup(self, capability: ProviderCapability) -> tuple[ProviderExecutionRecord, ...]:
        """Return enabled records that advertise a capability."""
        return tuple(
            record
            for record in self._records.values()
            if record.enabled and record.capabilities.supports(capability)
        )

    def health_lookup(self, state: ProviderHealthState) -> tuple[ProviderExecutionRecord, ...]:
        """Return records in the requested health state."""
        return tuple(record for record in self._records.values() if record.health.state is state)

    def statistics(self) -> dict[str, int]:
        """Return registry statistics."""
        records = tuple(self._records.values())
        return {
            "registered_providers": len(records),
            "enabled_providers": sum(1 for record in records if record.enabled),
            "healthy_providers": sum(
                1 for record in records if record.health.state is ProviderHealthState.HEALTHY
            ),
        }

    def load_from_provider_manager(self, provider_manager: Any) -> None:
        """Import provider metadata from the existing ProviderManager."""
        if provider_manager is None or not hasattr(provider_manager, "registry"):
            return
        for source_record in provider_manager.registry.all():
            provider = getattr(source_record, "provider", None)
            provider_id = getattr(getattr(source_record, "config", None), "provider_id", None)
            if not provider_id:
                continue
            capabilities = ProviderCapabilities.from_router_capabilities(
                provider.capabilities() if provider is not None else None
            )
            health = ProviderExecutionHealth()
            if provider is not None and provider.is_available():
                health.mark_healthy(getattr(getattr(provider, "health", None), "latency_ms", 0.0))
            elif not getattr(getattr(source_record, "config", None), "enabled", True):
                health.state = ProviderHealthState.DISABLED
                health.message = "Provider is disabled."
            self.register(
                ProviderExecutionRecord(
                    provider_id=provider_id,
                    capabilities=capabilities,
                    health=health,
                    enabled=bool(getattr(getattr(source_record, "config", None), "enabled", True)),
                    configuration={"kind": str(getattr(getattr(source_record, "config", None), "kind", ""))},
                )
            )
