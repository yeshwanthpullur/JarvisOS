"""Example research agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_profile import AgentProfile, AgentType
from agents.base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    """Architecture-only research agent."""


PROFILE = AgentProfile(name="Research Agent", agent_type=AgentType.RESEARCH, capabilities=(AgentCapability.RETRIEVAL,))
