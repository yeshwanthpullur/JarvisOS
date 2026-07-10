"""Example task agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_permissions import AgentPermission
from agents.agent_profile import AgentProfile, AgentType
from agents.base_agent import BaseAgent


class TaskAgent(BaseAgent):
    """Architecture-only task agent."""


PROFILE = AgentProfile(name="Task Agent", agent_type=AgentType.TASK, capabilities=(AgentCapability.TASKS,), permissions=(AgentPermission.TASKS,))
