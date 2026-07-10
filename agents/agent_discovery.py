"""Agent discovery contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from agents.agent_profile import AgentProfile
from agents.base_agent import BaseAgent


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    """Discovered agent class and profile metadata."""

    agent_class: Type[BaseAgent]
    profile: AgentProfile


class AgentDiscovery:
    """In-memory discovery source for built-in and plugin-provided agents."""

    def __init__(self) -> None:
        self._definitions: list[AgentDefinition] = []

    def add_definition(self, definition: AgentDefinition) -> None:
        """Add an agent definition."""
        self._definitions.append(definition)

    def discover(self) -> tuple[AgentDefinition, ...]:
        """Return discovered agent definitions."""
        return tuple(self._definitions)
