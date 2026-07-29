"""Agent execution result model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class AgentResultStatus(StrEnum):
    """Normalized multi-agent execution statuses."""

    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class AgentResult:
    """Normalized result envelope for agent and coordination execution."""

    agent_id: str
    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    coordination_id: str | None = None
    parent_request_id: str | None = None
    subtask_id: str | None = None
    status: AgentResultStatus = AgentResultStatus.COMPLETED
    content: str = ""
    structured_data: dict[str, Any] = field(default_factory=dict)
    evidence: tuple[dict[str, Any], ...] = ()
    sources: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    confidence: float = 0.0
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    provider_metadata: dict[str, Any] = field(default_factory=dict)
    tool_metadata: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: float = 0.0
    retry_count: int = 0

    def __post_init__(self) -> None:
        """Keep legacy construction truthful when success is false."""
        if not self.success and self.status is AgentResultStatus.COMPLETED:
            object.__setattr__(self, "status", AgentResultStatus.FAILED)
