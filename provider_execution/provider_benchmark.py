"""Provider benchmark ranking interfaces."""

from __future__ import annotations

from provider_execution.provider_registry import ProviderExecutionRecord


class ProviderBenchmark:
    """Ranks providers by execution metadata without running benchmarks."""

    initialized = True

    def latency_ranking(self, records: tuple[ProviderExecutionRecord, ...]) -> tuple[ProviderExecutionRecord, ...]:
        """Rank providers by observed latency."""
        return tuple(sorted(records, key=lambda record: record.health.latency_ms))

    def capability_ranking(self, records: tuple[ProviderExecutionRecord, ...]) -> tuple[ProviderExecutionRecord, ...]:
        """Rank providers by broad advertised capability count."""
        return tuple(sorted(records, key=lambda record: len(record.capabilities.models), reverse=True))

    def reliability_ranking(self, records: tuple[ProviderExecutionRecord, ...]) -> tuple[ProviderExecutionRecord, ...]:
        """Rank providers by reliability score."""
        return tuple(sorted(records, key=lambda record: record.metrics.reliability_score, reverse=True))

    def cost_ranking(self, records: tuple[ProviderExecutionRecord, ...]) -> tuple[ProviderExecutionRecord, ...]:
        """Rank providers by estimated cumulative cost."""
        return tuple(sorted(records, key=lambda record: record.metrics.estimated_cost))

    def performance_ranking(self, records: tuple[ProviderExecutionRecord, ...]) -> tuple[ProviderExecutionRecord, ...]:
        """Rank providers by performance score."""
        return tuple(sorted(records, key=lambda record: record.metrics.performance_score, reverse=True))

    def department_ranking(
        self,
        records: tuple[ProviderExecutionRecord, ...],
        department: str | None,
    ) -> tuple[ProviderExecutionRecord, ...]:
        """Rank providers with a future department preference hook."""
        if department is None:
            return records
        return tuple(sorted(records, key=lambda record: record.metadata.get("department") != department))

    def historical_ranking(self, records: tuple[ProviderExecutionRecord, ...]) -> tuple[ProviderExecutionRecord, ...]:
        """Rank providers by historical success metadata."""
        return tuple(sorted(records, key=lambda record: record.metrics.responses, reverse=True))
