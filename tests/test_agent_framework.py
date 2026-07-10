"""Tests for the JARVIS OS Agent Framework architecture."""

from __future__ import annotations

import unittest

from agents import (
    AgentBus,
    AgentCapability,
    AgentCheckpointStore,
    AgentContext,
    AgentDefinition,
    AgentEvent,
    AgentEventCategory,
    AgentExecutor,
    AgentFactory,
    AgentGoal,
    AgentLoader,
    AgentManager,
    AgentMessage,
    AgentMessageStatus,
    AgentOrchestrator,
    AgentPermission,
    AgentPermissionSet,
    AgentProfile,
    AgentRegistry,
    AgentRouter,
    AgentScheduler,
    AgentState,
    AgentStatus,
    AgentSupervisor,
    AgentTask,
    AgentTeam,
    AgentTeamType,
    AgentType,
    BaseAgent,
    ScheduledAgentWork,
    TrustLevel,
    validate_transition,
)
from agents.agent_planning import AgentPlanningInterface
from agents.agent_reasoning import AgentReasoningInterface
from agents.agent_reflection import AgentReflectionInterface


class TestAgent(BaseAgent):
    """Small concrete agent for framework tests."""


class NotAnAgent:
    """Invalid class used by factory validation tests."""


def profile(
    agent_id: str = "agent-1",
    *,
    name: str = "Test Agent",
    agent_type: AgentType = AgentType.CUSTOM,
    capabilities: tuple[AgentCapability, ...] = (),
    permissions: tuple[AgentPermission, ...] = (),
    priority: int = 100,
    dependencies: tuple[str, ...] = (),
) -> AgentProfile:
    """Create a deterministic profile."""
    return AgentProfile(
        agent_id=agent_id,
        name=name,
        agent_type=agent_type,
        capabilities=capabilities,
        permissions=permissions,
        priority=priority,
        dependencies=dependencies,
        trust_level=TrustLevel.CORE,
    )


class AgentFrameworkTests(unittest.TestCase):
    """Unit tests for agent framework components."""

    def make_agent(self, agent_id: str = "agent-1", **kwargs: object) -> TestAgent:
        """Create a test agent."""
        return TestAgent(profile(agent_id, **kwargs), AgentContext())

    def test_profile_serializes(self) -> None:
        data = profile(
            capabilities=(AgentCapability.PLANNING,),
            permissions=(AgentPermission.TASKS,),
        ).to_dict()
        self.assertEqual(data["agent_id"], "agent-1")
        self.assertEqual(data["capabilities"], ["planning"])
        self.assertEqual(data["permissions"], ["tasks"])

    def test_permission_set_allows_present_permission(self) -> None:
        permissions = AgentPermissionSet((AgentPermission.MEMORY,))
        permissions.require(AgentPermission.MEMORY)
        self.assertTrue(permissions.has(AgentPermission.MEMORY))

    def test_permission_set_rejects_missing_permission(self) -> None:
        permissions = AgentPermissionSet()
        with self.assertRaises(PermissionError):
            permissions.require(AgentPermission.SYSTEM)

    def test_valid_lifecycle_transition(self) -> None:
        validate_transition(AgentState.CREATED, AgentState.INITIALIZED)

    def test_invalid_lifecycle_transition(self) -> None:
        with self.assertRaises(ValueError):
            validate_transition(AgentState.CREATED, AgentState.RUNNING)

    def test_factory_creates_agent(self) -> None:
        agent = AgentFactory().create_agent(TestAgent, profile(), AgentContext())
        self.assertIsInstance(agent, BaseAgent)
        self.assertEqual(agent.agent_id, "agent-1")

    def test_factory_rejects_invalid_class(self) -> None:
        with self.assertRaises(TypeError):
            AgentFactory().create_agent(NotAnAgent, profile(), AgentContext())  # type: ignore[arg-type]

    def test_agent_initializes(self) -> None:
        agent = self.make_agent()
        agent.initialize()
        self.assertEqual(agent.state, AgentState.INITIALIZED)
        self.assertEqual(agent.status, AgentStatus.INITIALIZING)

    def test_agent_start_sets_running_state(self) -> None:
        agent = self.make_agent()
        agent.initialize()
        agent.start()
        self.assertEqual(agent.state, AgentState.RUNNING)
        self.assertEqual(agent.status, AgentStatus.RUNNING)

    def test_agent_pause_and_resume(self) -> None:
        agent = self.make_agent()
        agent.initialize()
        agent.start()
        agent.pause()
        agent.resume()
        self.assertEqual(agent.state, AgentState.RUNNING)

    def test_agent_sleep_and_wake(self) -> None:
        agent = self.make_agent()
        agent.initialize()
        agent.start()
        agent.sleep()
        agent.wake()
        self.assertEqual(agent.state, AgentState.READY)

    def test_agent_heartbeat_updates_health(self) -> None:
        agent = self.make_agent()
        agent.heartbeat()
        self.assertEqual(agent.health().status, AgentStatus.HEALTHY)
        self.assertIsNotNone(agent.last_heartbeat)

    def test_checkpoint_store_saves_latest_checkpoint(self) -> None:
        store = AgentCheckpointStore()
        context = AgentContext(checkpoint_store=store)
        agent = TestAgent(profile(), context)
        checkpoint = agent.checkpoint()
        self.assertEqual(store.latest(agent.agent_id), checkpoint)

    def test_agent_restore_checkpoint(self) -> None:
        agent = self.make_agent()
        checkpoint = agent.checkpoint()
        agent.restore(checkpoint)
        self.assertEqual(agent.state, AgentState.CREATED)

    def test_agent_execute_records_metrics(self) -> None:
        agent = self.make_agent()
        result = agent.execute({"ok": True})
        self.assertTrue(result.success)
        self.assertEqual(agent.metrics.execution_count, 1)

    def test_registry_registers_and_lists_agents(self) -> None:
        registry = AgentRegistry()
        agent = self.make_agent()
        registry.register(agent)
        self.assertEqual(registry.get(agent.agent_id), agent)
        self.assertEqual(registry.list_agents(), (agent,))

    def test_registry_filters_by_capability(self) -> None:
        agent = self.make_agent(capabilities=(AgentCapability.CODING,))
        registry = AgentRegistry()
        registry.register(agent)
        self.assertEqual(registry.filter_by_capability(AgentCapability.CODING), (agent,))

    def test_registry_filters_by_type(self) -> None:
        agent = self.make_agent(agent_type=AgentType.PLANNER)
        registry = AgentRegistry()
        registry.register(agent)
        self.assertEqual(registry.filter_by_type(AgentType.PLANNER), (agent,))

    def test_registry_filters_by_permission(self) -> None:
        agent = self.make_agent(permissions=(AgentPermission.KNOWLEDGE,))
        registry = AgentRegistry()
        registry.register(agent)
        self.assertEqual(registry.filter_by_permission(AgentPermission.KNOWLEDGE), (agent,))

    def test_registry_disable_marks_record_and_agent(self) -> None:
        agent = self.make_agent()
        registry = AgentRegistry()
        registry.register(agent)
        registry.disable(agent.agent_id)
        self.assertFalse(registry.require(agent.agent_id).enabled)
        self.assertEqual(agent.state, AgentState.DISABLED)

    def test_loader_respects_dependency_order(self) -> None:
        loader = AgentLoader()
        loader.add_definition(AgentDefinition(TestAgent, profile("agent-b", dependencies=("agent-a",))))
        loader.add_definition(AgentDefinition(TestAgent, profile("agent-a")))
        loaded = loader.load(AgentContext())
        self.assertEqual([agent.agent_id for agent in loaded], ["agent-a", "agent-b"])

    def test_loader_rejects_missing_dependency(self) -> None:
        loader = AgentLoader()
        loader.add_definition(AgentDefinition(TestAgent, profile("agent-b", dependencies=("missing",))))
        with self.assertRaises(ValueError):
            loader.load(AgentContext())

    def test_bus_routes_message_to_handler(self) -> None:
        bus = AgentBus()
        received: list[AgentMessage] = []
        bus.register_message_handler("receiver", received.append)
        message = AgentMessage(sender="sender", receiver="receiver")
        self.assertTrue(bus.route_message(message))
        self.assertEqual(message.status, AgentMessageStatus.DELIVERED)
        self.assertEqual(received, [message])

    def test_bus_fails_unknown_receiver(self) -> None:
        message = AgentMessage(sender="sender", receiver="missing")
        self.assertFalse(AgentBus().route_message(message))
        self.assertEqual(message.status, AgentMessageStatus.FAILED)

    def test_bus_publish_event(self) -> None:
        bus = AgentBus()
        received: list[AgentEvent] = []
        bus.subscribe(AgentEventCategory.HEALTH.value, received.append)
        event = AgentEvent(source="agent", category=AgentEventCategory.HEALTH)
        bus.publish(event)
        self.assertEqual(received, [event])

    def test_router_selects_highest_priority_capable_agent(self) -> None:
        registry = AgentRegistry()
        slow = self.make_agent("slow", capabilities=(AgentCapability.PLANNING,), priority=50)
        fast = self.make_agent("fast", capabilities=(AgentCapability.PLANNING,), priority=10)
        registry.register(slow)
        registry.register(fast)
        self.assertEqual(AgentRouter(registry).select_by_capability(AgentCapability.PLANNING), fast)

    def test_router_rejects_invalid_route(self) -> None:
        router = AgentRouter(AgentRegistry())
        with self.assertRaises(LookupError):
            router.route_message(AgentMessage(sender="a", receiver="b"))

    def test_scheduler_returns_priority_order(self) -> None:
        scheduler = AgentScheduler()
        scheduler.schedule(ScheduledAgentWork(agent_id="b", priority=20))
        scheduler.schedule(ScheduledAgentWork(agent_id="a", priority=1))
        self.assertEqual(scheduler.next_work().agent_id, "a")  # type: ignore[union-attr]

    def test_scheduler_pause_and_resume(self) -> None:
        scheduler = AgentScheduler()
        scheduler.schedule(ScheduledAgentWork(agent_id="a"))
        scheduler.pause()
        self.assertIsNone(scheduler.next_work())
        scheduler.resume()
        self.assertEqual(scheduler.next_work().agent_id, "a")  # type: ignore[union-attr]

    def test_scheduler_cancel_removes_work(self) -> None:
        scheduler = AgentScheduler()
        scheduler.schedule(ScheduledAgentWork(agent_id="a"))
        scheduler.cancel("a")
        self.assertEqual(scheduler.queue_length(), 0)

    def test_executor_validates_work(self) -> None:
        with self.assertRaises(ValueError):
            AgentExecutor().prepare(ScheduledAgentWork(agent_id=""))

    def test_executor_records_history(self) -> None:
        executor = AgentExecutor()
        result = executor.execute(ScheduledAgentWork(agent_id="a"))
        self.assertTrue(result.success)
        self.assertEqual(executor.history, [result])

    def test_supervisor_reports_failed_agents(self) -> None:
        registry = AgentRegistry()
        agent = self.make_agent()
        agent.status = AgentStatus.FAILED
        registry.register(agent)
        report = AgentSupervisor(registry).report()
        self.assertEqual(report.failed_agents, 1)
        self.assertEqual(report.restart_candidates, ("agent-1",))

    def test_orchestrator_accepts_objective(self) -> None:
        goal = AgentGoal(description="architecture only")
        plan = AgentOrchestrator().receive_objective(goal)
        self.assertEqual(plan.goal, goal)
        self.assertEqual(plan.tasks, ())

    def test_team_stores_metadata(self) -> None:
        team = AgentTeam(members=("a", "b"), leader="a", team_type=AgentTeamType.PAIR)
        self.assertEqual(team.members, ("a", "b"))
        self.assertEqual(team.team_type, AgentTeamType.PAIR)

    def test_manager_initializes_framework_services(self) -> None:
        manager = AgentManager()
        stats = manager.initialize()
        self.assertTrue(manager.initialized)
        self.assertEqual(stats.scheduler_status, "ready")
        self.assertEqual(stats.bus_status, "ready")

    def test_manager_create_start_and_shutdown_agent(self) -> None:
        manager = AgentManager()
        manager.initialize()
        agent = manager.create_agent(TestAgent, profile())
        manager.initialize_agent(agent.agent_id)
        manager.start_agent(agent.agent_id)
        self.assertEqual(manager.statistics().running_agents, 1)
        manager.shutdown_agent(agent.agent_id)
        self.assertEqual(agent.state, AgentState.SHUTDOWN)

    def test_context_preserves_references(self) -> None:
        memory = object()
        context = AgentContext(memory_manager=memory)
        self.assertIs(context.memory_manager, memory)

    def test_integration_interfaces_report_availability(self) -> None:
        from agents import AgentMemoryInterface

        self.assertFalse(AgentMemoryInterface().is_available())
        self.assertTrue(AgentMemoryInterface(object()).is_available())

    def test_reasoning_interface_is_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError):
            AgentReasoningInterface().reason({})

    def test_planning_interface_is_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError):
            AgentPlanningInterface().plan({})

    def test_reflection_interface_is_placeholder(self) -> None:
        with self.assertRaises(NotImplementedError):
            AgentReflectionInterface().reflect({})

    def test_examples_inherit_base_agent(self) -> None:
        from agents.examples.browser_agent import BrowserAgent
        from agents.examples.coding_agent import CodingAgent
        from agents.examples.conversation_agent import ConversationAgent
        from agents.examples.knowledge_agent import KnowledgeAgent
        from agents.examples.memory_agent import MemoryAgent
        from agents.examples.phone_agent import PhoneAgent
        from agents.examples.planner_agent import PlannerAgent
        from agents.examples.research_agent import ResearchAgent
        from agents.examples.system_agent import SystemAgent
        from agents.examples.task_agent import TaskAgent
        from agents.examples.vision_agent import VisionAgent

        for agent_class in (
            PlannerAgent,
            ResearchAgent,
            MemoryAgent,
            KnowledgeAgent,
            TaskAgent,
            CodingAgent,
            ConversationAgent,
            BrowserAgent,
            VisionAgent,
            PhoneAgent,
            SystemAgent,
        ):
            self.assertTrue(issubclass(agent_class, BaseAgent))

    def test_manager_registers_agent_message_handler(self) -> None:
        manager = AgentManager()
        manager.initialize()
        agent = manager.create_agent(TestAgent, profile())
        message = AgentMessage(sender="tester", receiver=agent.agent_id)
        self.assertTrue(manager.bus.route_message(message))
        self.assertEqual(agent.metrics.messages_received, 1)

    def test_agent_task_metadata_is_created(self) -> None:
        task = AgentTask(name="delegate", assigned_agent="agent-1")
        self.assertEqual(task.name, "delegate")
        self.assertEqual(task.assigned_agent, "agent-1")


if __name__ == "__main__":
    unittest.main()
