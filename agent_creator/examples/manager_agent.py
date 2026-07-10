"""Manager generated-agent example."""

from agents import BaseAgent
from agent_creator.blueprint import ManagerBlueprint


class ManagerExampleAgent(BaseAgent):
    """Example manager agent shell."""


BLUEPRINT = ManagerBlueprint()

