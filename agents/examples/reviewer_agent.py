"""Built-in safe reviewer agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_permissions import AgentPermission
from agents.agent_profile import AgentProfile, AgentType, TrustLevel
from agents.base_agent import BaseAgent


class ReviewerAgent(BaseAgent):
    """Reviews provider-generated work without tool or mutation authority."""


PROFILE = AgentProfile(
    agent_id="core-reviewer",
    name="Reviewer Agent",
    description="Reviews an authorized agent result for correctness and omissions.",
    agent_type=AgentType.OBSERVER,
    capabilities=(AgentCapability.REASONING, AgentCapability.REFLECTION, AgentCapability.REPORTING),
    permissions=(AgentPermission.PROVIDERS,),
    trust_level=TrustLevel.CORE,
)
