"""Supervisor generated-agent example."""

from agents import BaseAgent
from agent_creator.blueprint import SupervisorBlueprint


class SupervisorExampleAgent(BaseAgent):
    """Example supervisor agent shell."""


BLUEPRINT = SupervisorBlueprint()

