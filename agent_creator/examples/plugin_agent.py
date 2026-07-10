"""Plugin generated-agent example."""

from agents import BaseAgent
from agent_creator.blueprint import UtilityBlueprint


class PluginExampleAgent(BaseAgent):
    """Example plugin-provided agent shell."""


BLUEPRINT = UtilityBlueprint()

