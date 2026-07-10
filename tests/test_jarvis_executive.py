"""Tests for the Executive JARVIS Core."""

from __future__ import annotations

import unittest

from jarvis import (
    ExecutionStrategy,
    JarvisContext,
    JarvisCore,
    JarvisDecisionEngine,
    JarvisDispatcher,
    JarvisIntentEngine,
    JarvisIntentType,
    JarvisManager,
    JarvisRequest,
    JarvisRuntime,
    JarvisState,
)
from jarvis.jarvis_cache import JarvisCache
from jarvis.jarvis_cli import JarvisCLI
from jarvis.jarvis_command import JarvisCommand
from jarvis.jarvis_configuration import JarvisConfiguration
from jarvis.jarvis_controller import JarvisController
from jarvis.jarvis_department_registry import JarvisDepartmentRegistry
from jarvis.jarvis_departments import CORE_DEPARTMENTS, JarvisDepartment
from jarvis.jarvis_diagnostics import JarvisDiagnostics
from jarvis.jarvis_errors import JarvisErrorRecord
from jarvis.jarvis_event_bus import JarvisEventBus
from jarvis.jarvis_events import JarvisEvent, JarvisEventType
from jarvis.jarvis_executor import JarvisExecutor
from jarvis.jarvis_goal_manager import JarvisGoalManager
from jarvis.jarvis_health import JarvisHealth
from jarvis.jarvis_history import JarvisHistory
from jarvis.jarvis_intent_engine import IntentMetadata
from jarvis.jarvis_knowledge import JarvisKnowledge
from jarvis.jarvis_lifecycle import JarvisLifecycle
from jarvis.jarvis_logger import JarvisLogger
from jarvis.jarvis_memory import JarvisMemory
from jarvis.jarvis_metrics import JarvisMetrics
from jarvis.jarvis_orchestrator import JarvisOrchestrator
from jarvis.jarvis_planning import JarvisPlanning
from jarvis.jarvis_plugins import JarvisPlugins
from jarvis.jarvis_profile import JarvisProfile, SystemProfile, UserProfile, WorkspaceProfile
from jarvis.jarvis_providers import JarvisProviders
from jarvis.jarvis_reasoning import JarvisReasoning, JarvisReasoningRequest
from jarvis.jarvis_recovery_manager import JarvisRecoveryManager
from jarvis.jarvis_registry import JarvisRegistry
from jarvis.jarvis_response import JarvisResponse
from jarvis.jarvis_response_builder import JarvisResponseBuilder
from jarvis.jarvis_response_formatter import JarvisResponseFormatter
from jarvis.jarvis_router import JarvisRouter
from jarvis.jarvis_session import JarvisSession
from jarvis.jarvis_skills import JarvisSkillRecord, JarvisSkills
from jarvis.jarvis_supervisor import JarvisSupervisor
from jarvis.jarvis_tasks import JarvisTasks
from jarvis.jarvis_tools import JarvisToolRecord, JarvisTools
from jarvis.jarvis_types import JarvisComplexity, SessionType
from jarvis.jarvis_validator import JarvisValidator


class JarvisExecutiveTests(unittest.TestCase):
    """Executive JARVIS unit tests."""

    def test_runtime_initializes_and_starts(self) -> None:
        runtime = JarvisRuntime()
        runtime.initialize()
        runtime.start()
        self.assertEqual(runtime.state, JarvisState.IDLE)

    def test_runtime_pause_resume_shutdown(self) -> None:
        runtime = JarvisRuntime()
        runtime.initialize()
        runtime.start()
        runtime.pause()
        runtime.resume()
        runtime.stop()
        runtime.shutdown()
        self.assertEqual(runtime.state, JarvisState.SHUTDOWN)

    def test_runtime_checkpoint_restore(self) -> None:
        runtime = JarvisRuntime()
        runtime.initialize()
        checkpoint = runtime.checkpoint()
        runtime.restore(checkpoint)
        self.assertEqual(runtime.state, JarvisState.INITIALIZED)

    def test_lifecycle_validates_transition(self) -> None:
        lifecycle = JarvisLifecycle()
        lifecycle.transition_to(JarvisState.INITIALIZED)
        self.assertEqual(lifecycle.state, JarvisState.INITIALIZED)

    def test_lifecycle_rejects_invalid_transition(self) -> None:
        with self.assertRaises(ValueError):
            JarvisLifecycle().transition_to(JarvisState.EXECUTING)

    def test_request_defaults(self) -> None:
        request = JarvisRequest(content="hello")
        self.assertTrue(request.request_id)
        self.assertEqual(request.user_id, "local-user")

    def test_command_defaults(self) -> None:
        command = JarvisCommand(name="status")
        self.assertTrue(command.command_id)

    def test_session_close(self) -> None:
        session = JarvisSession(SessionType.CONVERSATION)
        session.close()
        self.assertIsNotNone(session.ended_at)

    def test_profiles_exist(self) -> None:
        self.assertEqual(JarvisProfile().name, "JARVIS Executive")
        self.assertEqual(UserProfile().user_id, "local-user")
        self.assertEqual(WorkspaceProfile().workspace_id, "local-workspace")
        self.assertEqual(SystemProfile().system_id, "jarvis-os")

    def test_context_holds_references(self) -> None:
        memory = object()
        context = JarvisContext(request_id="r1", memory_manager=memory)
        self.assertIs(context.memory_manager, memory)

    def test_intent_engine_detects_planning(self) -> None:
        intent = JarvisIntentEngine().identify(JarvisRequest(content="plan my work"))
        self.assertEqual(intent.primary_intent, JarvisIntentType.PLANNING)
        self.assertEqual(intent.execution_strategy, ExecutionStrategy.PLANNING)

    def test_intent_engine_detects_research(self) -> None:
        intent = JarvisIntentEngine().identify(JarvisRequest(content="research batteries"))
        self.assertEqual(intent.primary_intent, JarvisIntentType.RESEARCH)

    def test_intent_engine_detects_memory(self) -> None:
        intent = JarvisIntentEngine().identify(JarvisRequest(content="search memory"))
        self.assertEqual(intent.primary_intent, JarvisIntentType.MEMORY)

    def test_intent_engine_detects_task(self) -> None:
        intent = JarvisIntentEngine().identify(JarvisRequest(content="create task"))
        self.assertEqual(intent.primary_intent, JarvisIntentType.TASK)

    def test_intent_engine_detects_agent_creation(self) -> None:
        intent = JarvisIntentEngine().identify(JarvisRequest(content="create agent for fitness"))
        self.assertEqual(intent.primary_intent, JarvisIntentType.AGENT_CREATION)

    def test_decision_engine_uses_intent(self) -> None:
        intent = IntentMetadata(
            primary_intent=JarvisIntentType.PLANNING,
            complexity=JarvisComplexity.SIMPLE,
            required_departments=("planning",),
            execution_strategy=ExecutionStrategy.PLANNING,
        )
        decision = JarvisDecisionEngine().decide("goal", intent)
        self.assertEqual(decision.strategy, ExecutionStrategy.PLANNING)
        self.assertEqual(decision.department, "planning")

    def test_planning_creates_plan(self) -> None:
        intent = JarvisIntentEngine().identify(JarvisRequest(content="plan this"))
        decision = JarvisDecisionEngine().decide("plan this", intent)
        plan = JarvisPlanning().create_plan(decision)
        self.assertEqual(len(plan.steps), 1)

    def test_dispatcher_returns_metadata(self) -> None:
        request = JarvisRequest(content="plan this")
        intent = JarvisIntentEngine().identify(request)
        decision = JarvisDecisionEngine().decide(request.content, intent)
        plan = JarvisPlanning().create_plan(decision)
        result = JarvisDispatcher().dispatch(decision, plan)
        self.assertEqual(result.selected_department, "planning")

    def test_response_builder_builds_response(self) -> None:
        request = JarvisRequest(content="hello")
        intent = JarvisIntentEngine().identify(request)
        decision = JarvisDecisionEngine().decide(request.content, intent)
        plan = JarvisPlanning().create_plan(decision)
        dispatch = JarvisDispatcher().dispatch(decision, plan)
        response = JarvisResponseBuilder().build(request, decision, plan, dispatch)
        self.assertTrue(response.success)

    def test_response_formatter_returns_content(self) -> None:
        response = JarvisResponse(request_id="r1", content="ok")
        self.assertEqual(JarvisResponseFormatter().format(response), "ok")

    def test_controller_handles_request(self) -> None:
        response = JarvisController().handle(JarvisRequest(content="hello"), JarvisContext(request_id="r1"))
        self.assertTrue(response.success)

    def test_controller_rejects_empty_request(self) -> None:
        response = JarvisController().handle(JarvisRequest(content=" "), JarvisContext(request_id="r1"))
        self.assertFalse(response.success)

    def test_core_initializes_and_handles(self) -> None:
        core = JarvisCore()
        core.initialize()
        response = core.handle(JarvisRequest(content="plan a task"))
        self.assertEqual(response.execution_summary["strategy"], "planning")

    def test_manager_initializes_departments(self) -> None:
        manager = JarvisManager()
        stats = manager.initialize()
        self.assertEqual(stats.departments, len(CORE_DEPARTMENTS))

    def test_manager_records_history(self) -> None:
        manager = JarvisManager()
        manager.initialize()
        manager.handle_request(JarvisRequest(content="hello"))
        self.assertEqual(len(manager.history.list_responses()), 1)

    def test_event_bus_publish_subscribe(self) -> None:
        bus = JarvisEventBus()
        received: list[JarvisEvent] = []
        bus.subscribe(JarvisEventType.REQUEST_RECEIVED, received.append)
        event = JarvisEvent(event_type=JarvisEventType.REQUEST_RECEIVED, source="test")
        bus.publish(event)
        self.assertEqual(received, [event])

    def test_event_bus_unsubscribe(self) -> None:
        bus = JarvisEventBus()
        received: list[JarvisEvent] = []
        bus.subscribe(JarvisEventType.REQUEST_RECEIVED, received.append)
        bus.unsubscribe(JarvisEventType.REQUEST_RECEIVED, received.append)
        bus.publish(JarvisEvent(event_type=JarvisEventType.REQUEST_RECEIVED, source="test"))
        self.assertEqual(received, [])

    def test_registry_register_lookup_unregister(self) -> None:
        registry = JarvisRegistry()
        registry.register("x", object(), "test", ("cap",))
        self.assertIsNotNone(registry.lookup("x"))
        self.assertEqual(len(registry.capability_lookup("cap")), 1)
        self.assertTrue(registry.unregister("x"))

    def test_registry_statistics(self) -> None:
        registry = JarvisRegistry()
        registry.register("x", object(), "test")
        self.assertEqual(registry.statistics()["records"], 1)

    def test_department_registry_defaults(self) -> None:
        registry = JarvisDepartmentRegistry()
        registry.load_defaults()
        self.assertIsNotNone(registry.lookup("executive"))

    def test_department_registry_register_unregister(self) -> None:
        registry = JarvisDepartmentRegistry()
        registry.register(JarvisDepartment("custom", "Custom"))
        self.assertTrue(registry.unregister("custom"))

    def test_memory_adapter_availability(self) -> None:
        self.assertFalse(JarvisMemory().is_available())
        self.assertTrue(JarvisMemory(object()).is_available())

    def test_knowledge_adapter_availability(self) -> None:
        self.assertFalse(JarvisKnowledge().is_available())
        self.assertTrue(JarvisKnowledge(object()).is_available())

    def test_tasks_adapter_availability(self) -> None:
        self.assertFalse(JarvisTasks().is_available())
        self.assertTrue(JarvisTasks(object()).is_available())

    def test_plugins_adapter_availability(self) -> None:
        self.assertFalse(JarvisPlugins().is_available())
        self.assertTrue(JarvisPlugins(object()).is_available())

    def test_providers_adapter_availability(self) -> None:
        self.assertFalse(JarvisProviders().is_available())
        self.assertTrue(JarvisProviders(object()).is_available())

    def test_tools_register_lookup(self) -> None:
        tools = JarvisTools()
        tools.register(JarvisToolRecord("tool", "Tool"))
        self.assertEqual(tools.lookup("tool").name, "Tool")  # type: ignore[union-attr]

    def test_skills_register_lookup(self) -> None:
        skills = JarvisSkills()
        skills.register(JarvisSkillRecord("skill", "Skill"))
        self.assertEqual(skills.lookup("skill").name, "Skill")  # type: ignore[union-attr]

    def test_cache_set_get_clear(self) -> None:
        cache = JarvisCache()
        cache.set("response", "r1", "ok")
        self.assertEqual(cache.get("response", "r1"), "ok")
        cache.clear("response")
        self.assertIsNone(cache.get("response", "r1"))

    def test_validator_request(self) -> None:
        self.assertTrue(JarvisValidator().validate_request(JarvisRequest(content="ok")).valid)

    def test_validator_response(self) -> None:
        self.assertTrue(JarvisValidator().validate_response(JarvisResponse(request_id="r", content="ok")).valid)

    def test_reasoning_returns_metadata_only(self) -> None:
        result = JarvisReasoning().reason(JarvisReasoningRequest(prompt="why"))
        self.assertEqual(result.confidence, 0.0)

    def test_executor_returns_route(self) -> None:
        result = JarvisExecutor().execute("executive")
        self.assertEqual(result.output["route"], "executive")

    def test_router_returns_department_route(self) -> None:
        intent = JarvisIntentEngine().identify(JarvisRequest(content="plan"))
        decision = JarvisDecisionEngine().decide("plan", intent)
        self.assertEqual(JarvisRouter().route(decision), "planning")

    def test_orchestrator_coordinates(self) -> None:
        intent = JarvisIntentEngine().identify(JarvisRequest(content="plan"))
        decision = JarvisDecisionEngine().decide("plan", intent)
        plan = JarvisPlanning().create_plan(decision)
        self.assertEqual(JarvisOrchestrator().coordinate(decision, plan)["steps"], 1)

    def test_supervisor_reports_health(self) -> None:
        self.assertEqual(JarvisSupervisor().report(JarvisHealth()).health_status, "healthy")

    def test_recovery_manager_report(self) -> None:
        self.assertTrue(JarvisRecoveryManager().recover().success)

    def test_diagnostics_report(self) -> None:
        self.assertEqual(JarvisDiagnostics().report()["runtime"], "available")

    def test_metrics_defaults(self) -> None:
        self.assertEqual(JarvisMetrics().requests, 0)

    def test_health_heartbeat(self) -> None:
        health = JarvisHealth()
        health.heartbeat()
        self.assertIsNotNone(health.last_heartbeat)

    def test_health_mark_failed(self) -> None:
        health = JarvisHealth()
        health.mark_failed("x")
        self.assertEqual(health.status.value, "failed")

    def test_logger_factory(self) -> None:
        self.assertEqual(JarvisLogger().get_logger("test").name, "jarvis.test")

    def test_configuration_defaults(self) -> None:
        self.assertTrue(JarvisConfiguration().enabled)

    def test_history_records_response(self) -> None:
        history = JarvisHistory()
        response = JarvisResponse(request_id="r", content="ok")
        history.add(response)
        self.assertEqual(history.list_responses(), (response,))

    def test_goal_manager_lifecycle(self) -> None:
        goals = JarvisGoalManager()
        goal = goals.create("finish")
        goals.update(goal.goal_id, 0.5)
        goals.pause(goal.goal_id)
        goals.resume(goal.goal_id)
        goals.complete(goal.goal_id)
        self.assertEqual(goal.status, "completed")

    def test_cli_submits_through_core(self) -> None:
        core = JarvisCore()
        core.initialize()
        self.assertIn("JARVIS Executive received", JarvisCLI(core).submit("hello"))

    def test_error_record(self) -> None:
        record = JarvisErrorRecord(category="validation", message="bad")
        self.assertTrue(record.recoverable)

    def test_manager_statistics_requests_increment(self) -> None:
        manager = JarvisManager()
        manager.initialize()
        manager.handle_request(JarvisRequest(content="hello"))
        self.assertEqual(manager.statistics().requests, 1)

    def test_core_shutdown(self) -> None:
        core = JarvisCore()
        core.initialize()
        core.shutdown()
        self.assertFalse(core.initialized)


if __name__ == "__main__":
    unittest.main()
