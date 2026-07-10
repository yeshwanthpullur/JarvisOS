"""In-memory checkpoint store interface foundation."""

from __future__ import annotations

from agents.agent_checkpoint import AgentCheckpoint


class AgentCheckpointStore:
    """Stores agent checkpoints for future persistent recovery."""

    def __init__(self) -> None:
        self._checkpoints: dict[str, list[AgentCheckpoint]] = {}

    def save(self, checkpoint: AgentCheckpoint) -> None:
        """Save a checkpoint."""
        self._checkpoints.setdefault(checkpoint.agent_id, []).append(checkpoint)

    def latest(self, agent_id: str) -> AgentCheckpoint | None:
        """Return the latest checkpoint for an agent."""
        checkpoints = self._checkpoints.get(agent_id, [])
        return checkpoints[-1] if checkpoints else None

    def list_for_agent(self, agent_id: str) -> tuple[AgentCheckpoint, ...]:
        """List checkpoints for an agent."""
        return tuple(self._checkpoints.get(agent_id, ()))
