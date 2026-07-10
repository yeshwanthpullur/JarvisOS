"""Example system agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_permissions import AgentPermission
from agents.agent_profile import AgentProfile, AgentType, TrustLevel
from agents.base_agent import BaseAgent


class SystemAgent(BaseAgent):
    """Architecture-only system agent."""


PROFILE = AgentProfile(name="System Agent", agent_type=AgentType.SYSTEM, capabilities=(AgentCapability.MONITORING,), permissions=(AgentPermission.SYSTEM,), trust_level=TrustLevel.SYSTEM)
