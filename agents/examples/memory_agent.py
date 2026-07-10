"""Example memory agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_permissions import AgentPermission
from agents.agent_profile import AgentProfile, AgentType
from agents.base_agent import BaseAgent


class MemoryAgent(BaseAgent):
    """Architecture-only memory agent."""


PROFILE = AgentProfile(name="Memory Agent", agent_type=AgentType.MEMORY, capabilities=(AgentCapability.MEMORY,), permissions=(AgentPermission.MEMORY,))
