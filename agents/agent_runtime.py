"""Agent runtime state and statistics."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class AgentRuntimeState(StrEnum):
    """Runtime state labels."""

    STOPPED = "stopped"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"


@dataclass(slots=True)
class AgentRuntime:
    """Runtime metadata for future scaling and recovery."""

    state: AgentRuntimeState = AgentRuntimeState.STOPPED
    configuration: dict[str, Any] = field(default_factory=dict)
    recovery_metadata: dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        """Mark runtime running."""
        self.state = AgentRuntimeState.RUNNING

    def shutdown(self) -> None:
        """Mark runtime stopped."""
        self.state = AgentRuntimeState.STOPPED
