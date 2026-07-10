"""Metrics for provider execution decisions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProviderExecutionMetrics:
    """Aggregated execution metrics for one provider or model."""

    requests: int = 0
    responses: int = 0
    failures: int = 0
    retries: int = 0
    fallbacks: int = 0
    latency_ms: float = 0.0
    average_response_time_ms: float = 0.0
    estimated_tokens: int = 0
    estimated_cost: float = 0.0
    availability: float = 1.0
    usage: int = 0
    performance_score: float = 1.0
    reliability_score: float = 1.0

    def record_request(self, estimated_tokens: int = 0, estimated_cost: float = 0.0) -> None:
        """Record a planned provider request."""
        self.requests += 1
        self.usage += 1
        self.estimated_tokens += estimated_tokens
        self.estimated_cost += estimated_cost

    def record_response(self, latency_ms: float = 0.0) -> None:
        """Record a successful provider response."""
        self.responses += 1
        self.latency_ms = latency_ms
        self.average_response_time_ms = (
            ((self.average_response_time_ms * (self.responses - 1)) + latency_ms)
            / self.responses
        )

    def record_failure(self) -> None:
        """Record a failed provider attempt."""
        self.failures += 1
        total = max(1, self.requests)
        self.reliability_score = max(0.0, 1.0 - (self.failures / total))
