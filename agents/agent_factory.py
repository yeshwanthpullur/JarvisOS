"""Agent factory."""

from __future__ import annotations

from typing import Type

from agents.agent_context import AgentContext
from agents.agent_health import AgentHealth
from agents.agent_logger import AgentLoggerFactory
from agents.agent_metrics import AgentMetrics
from agents.agent_profile import AgentProfile
from agents.agent_validator import AgentValidator
from agents.base_agent import BaseAgent


class AgentFactory:
    """Creates and wires agent instances."""

    def __init__(
        self,
        validator: AgentValidator | None = None,
        logger_factory: AgentLoggerFactory | None = None,
    ) -> None:
        self._validator = validator or AgentValidator()
        self._logger_factory = logger_factory or AgentLoggerFactory()

    def create_agent(
        self,
        agent_class: Type[BaseAgent],
        profile: AgentProfile,
        context: AgentContext | None = None,
    ) -> BaseAgent:
        """Create an agent and attach runtime services."""
        result = self._validator.validate_class(agent_class)
        if not result.valid:
            raise TypeError("; ".join(result.errors))
        logger = self._logger_factory.get_logger(profile.agent_id)
        base_context = context or AgentContext()
        merged_context = AgentContext(
            settings=base_context.settings,
            memory_manager=base_context.memory_manager,
            knowledge_manager=base_context.knowledge_manager,
            task_manager=base_context.task_manager,
            brain_manager=base_context.brain_manager,
            plugin_manager=base_context.plugin_manager,
            provider_router=base_context.provider_router,
            logger=logger,
            metrics=base_context.metrics or AgentMetrics(),
            health=base_context.health or AgentHealth(),
            current_session=base_context.current_session,
            checkpoint_store=base_context.checkpoint_store,
            runtime=base_context.runtime,
        )
        agent = agent_class(profile, merged_context)
        validation = self._validator.validate_agent(agent)
        if not validation.valid:
            raise ValueError("; ".join(validation.errors))
        return agent
