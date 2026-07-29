"""Example planner agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_permissions import AgentPermission
from agents.agent_profile import AgentProfile, AgentType, TrustLevel
from agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """Architecture-only planner agent."""


PROFILE = AgentProfile(
    agent_id="core-planner",
    name="Planner Agent",
    description="Produces bounded, non-mutating plans through the provider framework.",
    agent_type=AgentType.PLANNER,
    capabilities=(AgentCapability.PLANNING, AgentCapability.REASONING, AgentCapability.REPORTING),
    permissions=(AgentPermission.PROVIDERS,),
    trust_level=TrustLevel.CORE,
)
