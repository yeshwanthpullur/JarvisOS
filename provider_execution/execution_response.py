"""Provider execution response envelope."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class ProviderExecutionResponse:
    """Structured result returned by the provider execution framework."""

    response: str
    provider: str | None = None
    model: str | None = None
    execution_time_ms: float = 0.0
    latency_ms: float = 0.0
    estimated_cost: float = 0.0
    token_metadata: dict[str, int] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    diagnostics: dict[str, Any] = field(default_factory=dict)
    references: tuple[str, ...] = ()
    statistics: dict[str, Any] = field(default_factory=dict)
    success: bool = True
