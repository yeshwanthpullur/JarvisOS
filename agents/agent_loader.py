"""Agent loader with dependency-aware ordering."""

from __future__ import annotations

import logging

from agents.agent_context import AgentContext
from agents.agent_discovery import AgentDefinition, AgentDiscovery
from agents.agent_factory import AgentFactory
from agents.base_agent import BaseAgent


class AgentLoader:
    """Loads discovered agent definitions."""

    def __init__(
        self,
        discovery: AgentDiscovery | None = None,
        factory: AgentFactory | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._discovery = discovery or AgentDiscovery()
        self._factory = factory or AgentFactory()
        self._logger = logger or logging.getLogger(__name__)

    def load(self, context: AgentContext | None = None) -> tuple[BaseAgent, ...]:
        """Instantiate agents in dependency-safe order."""
        definitions = list(self._discovery.discover())
        loaded: list[BaseAgent] = []
        loaded_ids: set[str] = set()
        while definitions:
            progressed = False
            for definition in tuple(definitions):
                if set(definition.profile.dependencies).issubset(loaded_ids):
                    agent = self._factory.create_agent(definition.agent_class, definition.profile, context)
                    loaded.append(agent)
                    loaded_ids.add(agent.agent_id)
                    definitions.remove(definition)
                    progressed = True
                    self._logger.info("agent_loaded agent_id=%s", agent.agent_id)
            if not progressed:
                raise ValueError("Agent dependency cycle or missing dependency detected.")
        return tuple(loaded)

    def add_definition(self, definition: AgentDefinition) -> None:
        """Add an agent definition to discovery."""
        self._discovery.add_definition(definition)
