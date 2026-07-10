"""Provider usage metrics."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ProviderMetrics:
    """Aggregated provider metrics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    response_time_ms: float = 0.0
    requests: int = 0
    failures: int = 0

    def record_request(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        estimated_cost: float = 0.0,
        response_time_ms: float = 0.0,
    ) -> None:
        """Record request metrics."""
        self.prompt_tokens += prompt_tokens
        self.completion_tokens += completion_tokens
        self.total_tokens += prompt_tokens + completion_tokens
        self.estimated_cost += estimated_cost
        self.response_time_ms = response_time_ms
        self.requests += 1

    def record_failure(self) -> None:
        """Record a failed provider operation."""
        self.failures += 1
