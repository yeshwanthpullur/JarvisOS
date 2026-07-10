"""Provider selection logic for intelligent execution."""

from __future__ import annotations

import logging

from provider_execution.execution_request import ProviderExecutionRequest
from provider_execution.execution_strategy import ExecutionStrategy
from provider_execution.provider_health import ProviderHealthState
from provider_execution.provider_registry import ProviderExecutionRecord, ProviderExecutionRegistry


class ProviderSelector:
    """Selects providers using capability, health, cost, locality, and history metadata."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.initialized = True
        self._logger = logger or logging.getLogger(__name__)

    def select(
        self,
        request: ProviderExecutionRequest,
        registry: ProviderExecutionRegistry,
    ) -> ProviderExecutionRecord | None:
        """Select the best provider record for the request."""
        candidates = self.rank(request, registry)
        selected = candidates[0] if candidates else None
        if selected is not None:
            self._logger.info(
                "provider_execution_selected provider_id=%s execution_id=%s",
                selected.provider_id,
                request.execution_id,
            )
        return selected

    def rank(
        self,
        request: ProviderExecutionRequest,
        registry: ProviderExecutionRegistry,
    ) -> tuple[ProviderExecutionRecord, ...]:
        """Return providers ranked by explicit preference and operational metadata."""
        records = [
            record
            for record in registry.discover()
            if record.enabled and self._matches_capabilities(record, request)
        ]
        if request.provider:
            records.sort(key=lambda record: record.provider_id != request.provider)
        if request.strategy is ExecutionStrategy.LOCAL_FIRST:
            records.sort(key=lambda record: not bool(record.metadata.get("local")))
        if request.strategy is ExecutionStrategy.CLOUD_FIRST:
            records.sort(key=lambda record: bool(record.metadata.get("local")))
        records.sort(key=self._score, reverse=True)
        return tuple(records)

    def _matches_capabilities(
        self,
        record: ProviderExecutionRecord,
        request: ProviderExecutionRequest,
    ) -> bool:
        return all(record.capabilities.supports(capability) for capability in request.capabilities)

    def _score(self, record: ProviderExecutionRecord) -> float:
        health_bonus = {
            ProviderHealthState.HEALTHY: 2.0,
            ProviderHealthState.UNKNOWN: 1.0,
            ProviderHealthState.BUSY: 0.75,
            ProviderHealthState.DEGRADED: 0.5,
            ProviderHealthState.RECOVERING: 0.25,
            ProviderHealthState.UNAVAILABLE: -1.0,
            ProviderHealthState.DISABLED: -2.0,
        }[record.health.state]
        priority_bonus = max(0, 10 - record.priority) / 10
        reliability_bonus = record.metrics.reliability_score
        latency_penalty = min(record.health.latency_ms / 10000, 1.0)
        return health_bonus + priority_bonus + reliability_bonus - latency_penalty
