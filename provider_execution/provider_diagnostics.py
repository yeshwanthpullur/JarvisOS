"""Diagnostic reports for provider execution."""

from __future__ import annotations

from provider_execution.provider_registry import ProviderExecutionRegistry


class ProviderDiagnostics:
    """Generates provider execution diagnostics."""

    initialized = True

    def health_report(self, registry: ProviderExecutionRegistry) -> dict[str, object]:
        """Return a health report."""
        return {"providers": {record.provider_id: record.health.state.value for record in registry.discover()}}

    def capability_report(self, registry: ProviderExecutionRegistry) -> dict[str, object]:
        """Return a capability report."""
        return {"providers": {record.provider_id: record.capabilities.metadata for record in registry.discover()}}

    def performance_report(self, registry: ProviderExecutionRegistry) -> dict[str, object]:
        """Return a performance report."""
        return {"providers": {record.provider_id: record.metrics.performance_score for record in registry.discover()}}

    def failure_report(self, registry: ProviderExecutionRegistry) -> dict[str, object]:
        """Return a failure report."""
        return {"providers": {record.provider_id: record.metrics.failures for record in registry.discover()}}

    def recovery_report(self, recovery_count: int = 0) -> dict[str, object]:
        """Return a recovery report."""
        return {"recovery_plans": recovery_count}

    def benchmark_report(self, registry: ProviderExecutionRegistry) -> dict[str, object]:
        """Return a benchmark report."""
        return {"providers": [record.provider_id for record in registry.discover()]}

    def statistics_report(self, registry: ProviderExecutionRegistry) -> dict[str, object]:
        """Return a statistics report."""
        return registry.statistics()

    def dependency_report(self) -> dict[str, object]:
        """Return a dependency report for future diagnostics."""
        return {"provider_router": "required", "provider_manager": "optional"}
