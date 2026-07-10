"""Agent registry, the source of truth for available agents."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from agents.agent_capabilities import AgentCapability
from agents.agent_permissions import AgentPermission
from agents.agent_profile import AgentType
from agents.agent_state import AgentState
from agents.agent_status import AgentStatus
from agents.base_agent import BaseAgent


@dataclass(slots=True)
class AgentRecord:
    """Registry record for an agent."""

    agent: BaseAgent
    enabled: bool = True


class AgentRegistry:
    """Registers, looks up, and filters agents."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._records: dict[str, AgentRecord] = {}
        self._logger = logger or logging.getLogger(__name__)

    def register(self, agent: BaseAgent) -> AgentRecord:
        """Register an agent."""
        record = AgentRecord(agent=agent)
        self._records[agent.agent_id] = record
        self._logger.info("agent_registered agent_id=%s name=%s", agent.agent_id, agent.profile.name)
        return record

    def remove(self, agent_id: str) -> bool:
        """Remove an agent."""
        removed = self._records.pop(agent_id, None) is not None
        self._logger.info("agent_removed agent_id=%s removed=%s", agent_id, removed)
        return removed

    def enable(self, agent_id: str) -> None:
        """Enable an agent."""
        self.require(agent_id).enabled = True

    def disable(self, agent_id: str) -> None:
        """Disable an agent."""
        record = self.require(agent_id)
        record.enabled = False
        record.agent.transition_to(AgentState.DISABLED)

    def reload(self, agent_id: str) -> BaseAgent:
        """Return registered agent for future reload support."""
        return self.require(agent_id).agent

    def get(self, agent_id: str) -> BaseAgent | None:
        """Lookup an agent by ID."""
        record = self._records.get(agent_id)
        return record.agent if record else None

    def require(self, agent_id: str) -> AgentRecord:
        """Return a record or raise."""
        record = self._records.get(agent_id)
        if record is None:
            raise KeyError(f"Agent not registered: {agent_id}")
        return record

    def list_agents(self) -> tuple[BaseAgent, ...]:
        """List all agents."""
        return tuple(record.agent for record in self._records.values())

    def filter_by_capability(self, capability: AgentCapability) -> tuple[BaseAgent, ...]:
        """Filter by capability."""
        return tuple(agent for agent in self.list_agents() if capability in agent.profile.capabilities)

    def filter_by_state(self, state: AgentState) -> tuple[BaseAgent, ...]:
        """Filter by state."""
        return tuple(agent for agent in self.list_agents() if agent.state is state)

    def filter_by_type(self, agent_type: AgentType) -> tuple[BaseAgent, ...]:
        """Filter by type."""
        return tuple(agent for agent in self.list_agents() if agent.profile.agent_type is agent_type)

    def filter_by_permission(self, permission: AgentPermission) -> tuple[BaseAgent, ...]:
        """Filter by permission."""
        return tuple(agent for agent in self.list_agents() if permission in agent.profile.permissions)

    def filter_by_status(self, status: AgentStatus) -> tuple[BaseAgent, ...]:
        """Filter by status."""
        return tuple(agent for agent in self.list_agents() if agent.status is status)

    def count_enabled(self) -> int:
        """Return enabled agent count."""
        return sum(1 for record in self._records.values() if record.enabled)
