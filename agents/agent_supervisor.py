"""Agent supervisor interfaces."""

from __future__ import annotations

from dataclasses import dataclass

from agents.agent_registry import AgentRegistry
from agents.agent_status import AgentStatus


@dataclass(frozen=True, slots=True)
class AgentSupervisorReport:
    """Supervisor report."""

    total_agents: int
    failed_agents: int
    unavailable_agents: int
    restart_candidates: tuple[str, ...]


class AgentSupervisor:
    """Monitors health and prepares recovery information."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry
        self.initialized = True

    def report(self) -> AgentSupervisorReport:
        """Create a supervisor report."""
        agents = self._registry.list_agents()
        failed = tuple(agent.agent_id for agent in agents if agent.status is AgentStatus.FAILED)
        unavailable = tuple(agent.agent_id for agent in agents if agent.status is AgentStatus.UNAVAILABLE)
        return AgentSupervisorReport(
            total_agents=len(agents),
            failed_agents=len(failed),
            unavailable_agents=len(unavailable),
            restart_candidates=failed,
        )

    def detect_stalled_agents(self) -> tuple[str, ...]:
        """Future stalled-agent detection interface."""
        return ()
