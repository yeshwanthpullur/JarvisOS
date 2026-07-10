"""Provider execution health models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from providers.provider_types import utc_now


class ProviderHealthState(StrEnum):
    """Health states used by the intelligent provider execution layer."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    BUSY = "busy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"
    RECOVERING = "recovering"


@dataclass(slots=True)
class ProviderExecutionHealth:
    """Provider health telemetry used during selection."""

    state: ProviderHealthState = ProviderHealthState.UNKNOWN
    availability: float = 1.0
    latency_ms: float = 0.0
    failure_rate: float = 0.0
    recovery_time_ms: float = 0.0
    timeouts: int = 0
    last_successful_request: datetime | None = None
    last_failure: datetime | None = None
    health_score: float = 1.0
    message: str = "Provider execution health is unknown."

    def mark_healthy(self, latency_ms: float = 0.0) -> None:
        """Record a healthy provider observation."""
        self.state = ProviderHealthState.HEALTHY
        self.latency_ms = latency_ms
        self.last_successful_request = utc_now()
        self.health_score = max(0.0, min(1.0, 1.0 - self.failure_rate))
        self.message = "Provider is healthy."

    def mark_failure(self, message: str) -> None:
        """Record a failure observation."""
        self.state = ProviderHealthState.DEGRADED
        self.last_failure = utc_now()
        self.failure_rate = min(1.0, self.failure_rate + 0.1)
        self.health_score = max(0.0, 1.0 - self.failure_rate)
        self.message = message
