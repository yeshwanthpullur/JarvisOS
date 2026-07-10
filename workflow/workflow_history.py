"""Workflow execution history."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class WorkflowHistoryRecord:
    workflow_id: str
    execution_id: str
    steps: tuple[str, ...]
    execution_order: tuple[str, ...]
    dependencies: tuple[str, ...]
    providers: tuple[str, ...]
    agents: tuple[str, ...]
    departments: tuple[str, ...]
    results: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    failures: tuple[str, ...] = ()
    recoveries: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class WorkflowHistory:
    initialized = True

    def __init__(self) -> None:
        self._records: list[WorkflowHistoryRecord] = []

    def append(self, record: WorkflowHistoryRecord) -> None:
        self._records.append(record)

    def list(self) -> tuple[WorkflowHistoryRecord, ...]:
        return tuple(self._records)
