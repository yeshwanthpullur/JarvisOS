"""Health model for Agent Creator."""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_creator.status import CreatorStatus
from agent_creator.utils import utc_now


@dataclass(slots=True)
class AgentCreatorHealth:
    """Health state for Agent Creator components."""

    status: CreatorStatus = CreatorStatus.READY
    last_check: str = field(default_factory=lambda: utc_now().isoformat())
    message: str = "Agent Creator ready."

    def mark_ready(self) -> None:
        """Mark creator health as ready."""
        self.status = CreatorStatus.READY
        self.last_check = utc_now().isoformat()

