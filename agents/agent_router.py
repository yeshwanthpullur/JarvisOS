"""Agent routing interfaces."""

from __future__ import annotations

from agents.agent_capabilities import AgentCapability
from agents.agent_message import AgentMessage
from agents.agent_registry import AgentRegistry
from agents.base_agent import BaseAgent


class AgentRouter:
    """Routes messages, tasks, and events to destination agents."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry
        self.initialized = True

    def select_by_capability(self, capability: AgentCapability) -> BaseAgent | None:
        """Select the highest-priority agent with a capability."""
        agents = self._registry.filter_by_capability(capability)
        if not agents:
            return None
        return sorted(agents, key=lambda agent: agent.profile.priority)[0]

    def validate_route(self, message: AgentMessage) -> bool:
        """Return whether a message route is valid."""
        return self._registry.get(message.receiver) is not None

    def route_message(self, message: AgentMessage) -> str:
        """Return destination agent ID for a message."""
        if not self.validate_route(message):
            raise LookupError(f"No destination agent for message: {message.receiver}")
        return message.receiver
