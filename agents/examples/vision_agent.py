"""Example vision agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_permissions import AgentPermission
from agents.agent_profile import AgentProfile, AgentType
from agents.base_agent import BaseAgent


class VisionAgent(BaseAgent):
    """Architecture-only vision agent."""


PROFILE = AgentProfile(name="Vision Agent", agent_type=AgentType.VISION, capabilities=(AgentCapability.VISION,), permissions=(AgentPermission.VISION,))
