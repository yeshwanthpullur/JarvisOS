"""Workflow metrics."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(slots=True)
class WorkflowMetrics:
    created: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0
    recovered: int = 0
    average_duration_ms: float = 0.0
    average_steps: float = 0.0
    parallel_executions: int = 0
    sequential_executions: int = 0
    recovery_count: int = 0
    success_rate: float = 1.0

    def statistics(self) -> dict[str, float | int]:
        return asdict(self)
