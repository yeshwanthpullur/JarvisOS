"""Central Agent Framework manager."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from agents.agent_bus import AgentBus
from agents.agent_context import AgentContext
from agents.agent_discovery import AgentDefinition
from agents.agent_executor import AgentExecutor
from agents.agent_factory import AgentFactory
from agents.agent_health import AgentHealth
from agents.agent_loader import AgentLoader
from agents.agent_metrics import AgentMetrics
from agents.agent_orchestrator import AgentOrchestrator
from agents.agent_profile import AgentProfile
from agents.agent_registry import AgentRegistry
from agents.agent_router import AgentRouter
from agents.agent_scheduler import AgentScheduler
from agents.agent_state import AgentState
from agents.agent_status import AgentStatus
from agents.agent_supervisor import AgentSupervisor
from agents.base_agent import BaseAgent


@dataclass(frozen=True, slots=True)
class AgentFrameworkStatistics:
    """Startup and runtime statistics for the Agent Framework."""

    registered_agents: int
    loaded_agents: int
    enabled_agents: int
    running_agents: int
    healthy_agents: int
    disabled_agents: int
    failed_agents: int
    scheduler_status: str
    supervisor_status: str
    orchestrator_status: str
    bus_status: str
    health_status: str


class AgentManager:
    """Central controller for all agents and agent services."""

    def __init__(
        self,
        context: AgentContext | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.context = context or AgentContext()
        self.registry = AgentRegistry(logger=self._logger)
        self.factory = AgentFactory()
        self.loader = AgentLoader(factory=self.factory, logger=self._logger)
        self.bus = AgentBus(logger=self._logger)
        self.router = AgentRouter(self.registry)
        self.scheduler = AgentScheduler()
        self.executor = AgentExecutor()
        self.supervisor = AgentSupervisor(self.registry)
        self.orchestrator = AgentOrchestrator()
        self.metrics = AgentMetrics()
        self.health = AgentHealth()
        self.initialized = False

    def initialize(self) -> AgentFrameworkStatistics:
        """Initialize the Agent Framework."""
        for agent in self.loader.load(self.context):
            self.register_agent(agent)
        self.initialized = True
        self.health.heartbeat()
        self._logger.info("agent_framework_initialized registered=%s", len(self.registry.list_agents()))
        return self.statistics()

    def add_definition(self, definition: AgentDefinition) -> None:
        """Add an agent definition for loading."""
        self.loader.add_definition(definition)

    def create_agent(
        self,
        agent_class: type[BaseAgent],
        profile: AgentProfile,
        context: AgentContext | None = None,
    ) -> BaseAgent:
        """Create and register an agent."""
        agent = self.factory.create_agent(agent_class, profile, context or self.context)
        self.register_agent(agent)
        return agent

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent and its message handler."""
        self.registry.register(agent)
        self.bus.register_message_handler(agent.agent_id, agent.on_message)

    def initialize_agent(self, agent_id: str) -> None:
        """Initialize one agent."""
        self.registry.require(agent_id).agent.initialize()

    def start_agent(self, agent_id: str) -> None:
        """Start one agent."""
        self.registry.require(agent_id).agent.start()

    def pause_agent(self, agent_id: str) -> None:
        """Pause one agent."""
        self.registry.require(agent_id).agent.pause()

    def resume_agent(self, agent_id: str) -> None:
        """Resume one agent."""
        self.registry.require(agent_id).agent.resume()

    def restart_agent(self, agent_id: str) -> None:
        """Restart one agent."""
        self.registry.require(agent_id).agent.restart()

    def shutdown_agent(self, agent_id: str) -> None:
        """Shutdown one agent."""
        self.registry.require(agent_id).agent.shutdown()

    def destroy_agent(self, agent_id: str) -> None:
        """Destroy one agent."""
        agent = self.registry.require(agent_id).agent
        if agent.state is not AgentState.SHUTDOWN:
            agent.shutdown()
        agent.transition_to(AgentState.DESTROYED)
        self.registry.remove(agent_id)

    def active_agents(self) -> tuple[BaseAgent, ...]:
        """Return running or busy agents."""
        return tuple(
            agent for agent in self.registry.list_agents() if agent.state in {AgentState.RUNNING, AgentState.BUSY}
        )

    def inactive_agents(self) -> tuple[BaseAgent, ...]:
        """Return inactive agents."""
        return tuple(
            agent for agent in self.registry.list_agents() if agent.state not in {AgentState.RUNNING, AgentState.BUSY}
        )

    def shutdown(self) -> None:
        """Shutdown all agents."""
        for agent in self.registry.list_agents():
            if agent.state not in {AgentState.SHUTDOWN, AgentState.DESTROYED}:
                try:
                    agent.shutdown()
                except ValueError:
                    agent.state = AgentState.SHUTDOWN
        self.initialized = False

    def statistics(self) -> AgentFrameworkStatistics:
        """Return Agent Framework statistics."""
        agents = self.registry.list_agents()
        return AgentFrameworkStatistics(
            registered_agents=len(agents),
            loaded_agents=len(agents),
            enabled_agents=self.registry.count_enabled(),
            running_agents=sum(1 for agent in agents if agent.state is AgentState.RUNNING),
            healthy_agents=sum(1 for agent in agents if agent.health().status is AgentStatus.HEALTHY),
            disabled_agents=sum(1 for agent in agents if agent.state is AgentState.DISABLED),
            failed_agents=sum(1 for agent in agents if agent.state is AgentState.FAILED),
            scheduler_status="ready" if self.scheduler.initialized else "unavailable",
            supervisor_status="ready" if self.supervisor.initialized else "unavailable",
            orchestrator_status="ready" if self.orchestrator.initialized else "unavailable",
            bus_status="ready" if self.bus.initialized else "unavailable",
            health_status=self.health.status.value,
        )
