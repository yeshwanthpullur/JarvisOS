"""Example conversation agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_profile import AgentProfile, AgentType
from agents.base_agent import BaseAgent


class ConversationAgent(BaseAgent):
    """Architecture-only conversation agent."""


PROFILE = AgentProfile(name="Conversation Agent", agent_type=AgentType.CONVERSATION, capabilities=(AgentCapability.CONVERSATION,))
