"""Runtime metadata for Agent Creator."""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_creator.status import CreatorStatus
from agent_creator.utils import utc_now


@dataclass(slots=True)
class AgentCreatorRuntime:
    """Runtime state for creator operations."""

    status: CreatorStatus = CreatorStatus.READY
    initialized_at: str = field(default_factory=lambda: utc_now().isoformat())
    operations_started: int = 0
    operations_completed: int = 0
    operations_failed: int = 0

