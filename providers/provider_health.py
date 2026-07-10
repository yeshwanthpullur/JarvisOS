"""Provider health tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from providers.provider_types import utc_now


@dataclass(slots=True)
class ProviderHealth:
    """Availability and reliability state for a provider."""

    available: bool = True
    latency_ms: float = 0.0
    failures: int = 0
    retry_count: int = 0
    last_successful_request: datetime | None = None
    message: str = "Provider interface available."

    def mark_success(self, latency_ms: float = 0.0) -> None:
        """Record a successful provider operation."""
        self.available = True
        self.latency_ms = latency_ms
        self.last_successful_request = utc_now()
        self.message = "Provider interface available."

    def mark_failure(self, message: str) -> None:
        """Record a provider failure."""
        self.available = False
        self.failures += 1
        self.message = message
