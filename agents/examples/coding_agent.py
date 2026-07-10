"""Example coding agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_profile import AgentProfile, AgentType
from agents.base_agent import BaseAgent


class CodingAgent(BaseAgent):
    """Architecture-only coding agent."""


PROFILE = AgentProfile(name="Coding Agent", agent_type=AgentType.CODING, capabilities=(AgentCapability.CODING,))
