"""Example knowledge agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_permissions import AgentPermission
from agents.agent_profile import AgentProfile, AgentType
from agents.base_agent import BaseAgent


class KnowledgeAgent(BaseAgent):
    """Architecture-only knowledge agent."""


PROFILE = AgentProfile(name="Knowledge Agent", agent_type=AgentType.KNOWLEDGE, capabilities=(AgentCapability.KNOWLEDGE,), permissions=(AgentPermission.KNOWLEDGE,))
