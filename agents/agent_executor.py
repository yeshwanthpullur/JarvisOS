"""Agent executor interfaces."""

from __future__ import annotations

from agents.agent_result import AgentResult
from agents.agent_scheduler import ScheduledAgentWork


class AgentExecutor:
    """Receives scheduled work and records metadata without performing work."""

    def __init__(self) -> None:
        self.history: list[AgentResult] = []
        self.initialized = True

    def prepare(self, work: ScheduledAgentWork) -> ScheduledAgentWork:
        """Validate and prepare execution metadata."""
        if not work.agent_id:
            raise ValueError("Scheduled work requires an agent ID.")
        return work

    def execute(self, work: ScheduledAgentWork) -> AgentResult:
        """Return an interface result without performing work."""
        self.prepare(work)
        result = AgentResult(agent_id=work.agent_id, success=True, output={"scheduled": True})
        self.history.append(result)
        return result

    def cancel(self, agent_id: str) -> None:
        """Future cancellation interface."""

    def rollback(self, agent_id: str) -> None:
        """Future rollback interface."""
