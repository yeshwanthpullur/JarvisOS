"""Example browser agent."""

from agents.agent_capabilities import AgentCapability
from agents.agent_permissions import AgentPermission
from agents.agent_profile import AgentProfile, AgentType
from agents.base_agent import BaseAgent


class BrowserAgent(BaseAgent):
    """Architecture-only browser agent."""


PROFILE = AgentProfile(name="Browser Agent", agent_type=AgentType.BROWSER, capabilities=(AgentCapability.BROWSER,), permissions=(AgentPermission.INTERNET,))
