"""Agent validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Type

from agents.base_agent import BaseAgent


@dataclass(frozen=True, slots=True)
class AgentValidationResult:
    """Agent validation result."""

    valid: bool
    errors: tuple[str, ...] = ()


class AgentValidator:
    """Validates agent classes and instances."""

    def validate_class(self, agent_class: Type[BaseAgent]) -> AgentValidationResult:
        """Validate that a class inherits BaseAgent."""
        if not issubclass(agent_class, BaseAgent):
            return AgentValidationResult(False, ("Agent class must inherit BaseAgent.",))
        return AgentValidationResult(True)

    def validate_agent(self, agent: BaseAgent) -> AgentValidationResult:
        """Validate an agent instance."""
        errors: list[str] = []
        if not agent.validate():
            errors.append("Agent metadata is invalid.")
        return AgentValidationResult(valid=not errors, errors=tuple(errors))
