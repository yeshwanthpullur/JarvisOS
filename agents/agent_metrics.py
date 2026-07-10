"""Agent metrics foundation."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class AgentMetrics:
    """Runtime metrics tracked for an agent."""

    execution_count: int = 0
    failure_count: int = 0
    restart_count: int = 0
    recovery_count: int = 0
    average_execution_time: float = 0.0
    maximum_execution_time: float = 0.0
    minimum_execution_time: float = 0.0
    messages_sent: int = 0
    messages_received: int = 0
    tasks_executed: int = 0
    tasks_failed: int = 0
    queue_length: int = 0
    health_score: float = 1.0
    future_token_usage: int = 0
    future_cost: float = 0.0
    future_model_usage: dict[str, int] | None = None
