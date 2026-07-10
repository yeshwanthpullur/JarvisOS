"""Example planner agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_profile import AgentProfile, AgentType
from agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    """Architecture-only planner agent."""


PROFILE = AgentProfile(
    name="Planner Agent",
    description="Future planning agent.",
    agent_type=AgentType.PLANNER,
    capabilities=(AgentCapability.PLANNING,),
)
