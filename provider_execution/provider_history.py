"""Execution history for provider routing decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from providers.provider_types import utc_now
from provider_execution.execution_strategy import ExecutionStrategy


@dataclass(frozen=True, slots=True)
class ProviderExecutionHistoryRecord:
    """Historical record for one provider execution decision."""

    execution_id: str
    provider: str | None
    model: str | None
    department: str | None
    agent: str | None
    execution_strategy: ExecutionStrategy
    latency_ms: float = 0.0
    estimated_cost: float = 0.0
    estimated_tokens: int = 0
    success: bool = True
    failure: str | None = None
    recovery: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=utc_now)


class ProviderExecutionHistory:
    """In-memory history for future analytics and persistence."""

    initialized = True

    def __init__(self) -> None:
        self._records: list[ProviderExecutionHistoryRecord] = []

    def append(self, record: ProviderExecutionHistoryRecord) -> None:
        """Append an execution history record."""
        self._records.append(record)

    def list(self) -> tuple[ProviderExecutionHistoryRecord, ...]:
        """Return all history records."""
        return tuple(self._records)

    def search(self, provider: str | None = None, success: bool | None = None) -> tuple[ProviderExecutionHistoryRecord, ...]:
        """Search execution history."""
        return tuple(
            record
            for record in self._records
            if (provider is None or record.provider == provider)
            and (success is None or record.success is success)
        )

    def statistics(self) -> dict[str, int]:
        """Return execution history statistics."""
        return {
            "executions": len(self._records),
            "successful_executions": sum(1 for record in self._records if record.success),
            "failed_executions": sum(1 for record in self._records if not record.success),
        }
