"""Health generated-agent example."""

from agents import BaseAgent
from agent_creator.blueprint import HealthBlueprint


class HealthExampleAgent(BaseAgent):
    """Example health agent shell."""


BLUEPRINT = HealthBlueprint()

