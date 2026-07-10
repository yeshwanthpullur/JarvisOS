"""Department generated-agent example."""

from agents import BaseAgent
from agent_creator.blueprint import DepartmentBlueprint


class DepartmentExampleAgent(BaseAgent):
    """Example department agent shell."""


BLUEPRINT = DepartmentBlueprint()

