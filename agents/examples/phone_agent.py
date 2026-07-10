"""Example phone agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_permissions import AgentPermission
from agents.agent_profile import AgentProfile, AgentType
from agents.base_agent import BaseAgent


class PhoneAgent(BaseAgent):
    """Architecture-only phone agent."""


PROFILE = AgentProfile(name="Phone Agent", agent_type=AgentType.PHONE, capabilities=(AgentCapability.PHONE,), permissions=(AgentPermission.MOBILE,))
