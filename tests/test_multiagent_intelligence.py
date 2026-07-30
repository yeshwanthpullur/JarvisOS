"""Behavioral coverage for governed Multi-Agent Intelligence."""

from __future__ import annotations

import logging
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from agents import (
    AgentCapability,
    AgentContext,
    AgentOrchestrator,
    AgentPermission,
    AgentProfile,
    AgentResultStatus,
    AgentState,
    CollaborationMode,
    CoordinationStatus,
    DelegatedSubtask,
    DelegationPlan,
    MultiAgentAssessment,
    MultiAgentLimits,
    MultiAgentMode,
    TrustLevel,
)
from agents.agent_manager import AgentManager
from agents.agent_registry import AgentRegistry
from agents.agent_status import AgentStatus
from agents.base_agent import BaseAgent
from commands import CommandManager
from conversation import ConversationContext, ConversationManager, ConversationSession
from jarvis import JarvisContext, JarvisRequest, JarvisResponse
from jarvis.jarvis_controller import JarvisController
from provider_execution import ProviderExecutionResponse


class FakeExecutionManager:
    def __init__(self, fail_agent: str | None = None) -> None:
        self.fail_agent = fail_agent
        self.requests: list[SimpleNamespace] = []

    def build_execution_request(self, intent: str, goal: str, **metadata: object) -> SimpleNamespace:
        request = SimpleNamespace(intent=intent, goal=goal, **metadata)
        self.requests.append(request)
        return request

    def execute_through_provider_router(self, request: SimpleNamespace) -> ProviderExecutionResponse:
        agent_id = request.metadata.get("agent_id")
        if agent_id == self.fail_agent:
            return ProviderExecutionResponse(response="provider failed", provider="local", model="test", success=False)
        if agent_id == "coordinator":
            content = "Synthesized authorized result."
        elif agent_id == "core-reviewer":
            content = "Review: the plan is supported, with one stated assumption."
        else:
            content = "Plan: provide a concise answer and state assumptions."
        return ProviderExecutionResponse(
            response=content,
            provider="local",
            model="llama-test",
            latency_ms=4.0,
            token_metadata={"total_tokens": 12},
            success=True,
        )


class TimeoutExecutionManager(FakeExecutionManager):
    def execute_through_provider_router(self, request: SimpleNamespace) -> ProviderExecutionResponse:
        return ProviderExecutionResponse(response="Provider timed out.", warnings=("timeout",), success=False)


def make_agent(
    agent_id: str,
    capabilities: tuple[AgentCapability, ...],
    *,
    permissions: tuple[AgentPermission, ...] = (AgentPermission.PROVIDERS,),
    trust: TrustLevel = TrustLevel.CORE,
) -> BaseAgent:
    agent = BaseAgent(
        AgentProfile(
            agent_id=agent_id,
            name=agent_id,
            capabilities=capabilities,
            permissions=permissions,
            trust_level=trust,
        )
    )
    agent.initialize()
    agent.start()
    return agent


def make_orchestrator(
    execution: FakeExecutionManager | None = None,
    workspace: Path | None = None,
) -> AgentOrchestrator:
    registry = AgentRegistry()
    registry.register(make_agent("core-planner", (AgentCapability.PLANNING, AgentCapability.REASONING)))
    registry.register(make_agent("core-reviewer", (AgentCapability.REFLECTION, AgentCapability.REASONING)))
    return AgentOrchestrator(registry, execution or FakeExecutionManager(), workspace_dir=workspace)


def assessment(mode: CollaborationMode = CollaborationMode.REVIEW) -> MultiAgentAssessment:
    return MultiAgentAssessment(True, "bounded review", ("planner", "reviewer"), mode, confidence=0.9)


class MultiAgentIntelligenceTests(unittest.TestCase):
    def test_simple_request_stays_single_agent(self) -> None:
        result = make_orchestrator().assess("What time is it?")
        self.assertFalse(result.requires_multi_agent)

    def test_explicit_complex_request_triggers_assessment(self) -> None:
        result = make_orchestrator().assess("Use a planner and reviewer to independently review this architecture.")
        self.assertTrue(result.requires_multi_agent)
        self.assertEqual(result.collaboration_mode, CollaborationMode.REVIEW)

    def test_planner_reviewer_request_is_not_intercepted_as_goal_review(self) -> None:
        class GoalManager:
            def prepare_request(self, *_args: object) -> SimpleNamespace:
                return SimpleNamespace(immediate_response="goal interception", metadata={})

        class Executive:
            def handle(self, request: JarvisRequest) -> JarvisResponse:
                return JarvisResponse(request_id=request.request_id, content="multi-agent path")

        manager = ConversationManager(jarvis_core=Executive(), goal_intelligence_manager=GoalManager())
        manager.initialize()
        response = manager.handle_input(
            "Use a planner and reviewer to produce and review a short checklist."
        )
        self.assertEqual(response.response, "multi-agent path")

    def test_multiagent_off_rejects_coordination(self) -> None:
        orchestrator = make_orchestrator()
        orchestrator.set_mode(MultiAgentMode.OFF)
        self.assertFalse(orchestrator.assess("Use multi-agent review.").requires_multi_agent)

    def test_confirm_mode_requires_approval_metadata(self) -> None:
        orchestrator = make_orchestrator()
        orchestrator.set_mode(MultiAgentMode.CONFIRM)
        self.assertFalse(orchestrator.assess("Use multi-agent review.").requires_multi_agent)
        self.assertTrue(orchestrator.assess("Use multi-agent review.", {"multiagent_approved": True}).requires_multi_agent)

    def test_collaboration_modes_are_selected_explicitly(self) -> None:
        orchestrator = make_orchestrator()
        cases = {
            "Run a bounded debate with multiple agents.": CollaborationMode.DEBATE,
            "Research and verify this claim.": CollaborationMode.RESEARCH_VERIFICATION,
            "Use a specialist panel for this.": CollaborationMode.SPECIALIST_PANEL,
            "Run these agents in parallel.": CollaborationMode.PARALLEL,
            "Use a planner and executor.": CollaborationMode.PLANNER_EXECUTOR,
        }
        for prompt, expected in cases.items():
            self.assertEqual(orchestrator.assess(prompt).collaboration_mode, expected)

    def test_capability_selection_uses_registry(self) -> None:
        orchestrator = make_orchestrator()
        selected = orchestrator.select_agents((AgentCapability.PLANNING,))
        self.assertEqual(tuple(item.agent_id for item in selected), ("core-planner",))

    def test_disabled_agent_is_rejected(self) -> None:
        orchestrator = make_orchestrator()
        orchestrator.registry.require("core-planner").enabled = False
        self.assertEqual(orchestrator.select_agents((AgentCapability.PLANNING,)), ())

    def test_unhealthy_agent_is_rejected(self) -> None:
        orchestrator = make_orchestrator()
        orchestrator.registry.get("core-planner").health_state.status = AgentStatus.FAILED  # type: ignore[union-attr]
        self.assertEqual(orchestrator.select_agents((AgentCapability.PLANNING,)), ())

    def test_unauthorized_agent_is_rejected(self) -> None:
        registry = AgentRegistry()
        registry.register(make_agent("no-provider", (AgentCapability.PLANNING,), permissions=()))
        orchestrator = AgentOrchestrator(registry, FakeExecutionManager())
        self.assertEqual(orchestrator.select_agents((AgentCapability.PLANNING,)), ())

    def test_untrusted_agent_is_rejected(self) -> None:
        registry = AgentRegistry()
        registry.register(make_agent("untrusted", (AgentCapability.PLANNING,), trust=TrustLevel.UNTRUSTED))
        orchestrator = AgentOrchestrator(registry, FakeExecutionManager())
        self.assertEqual(orchestrator.select_agents((AgentCapability.PLANNING,)), ())

    def test_plan_preserves_parent_and_unique_subtask_ids(self) -> None:
        plan = make_orchestrator().create_delegation_plan("Review this", "parent-1", assessment(), {})
        self.assertEqual(plan.parent_request_id, "parent-1")
        self.assertEqual(len({item.subtask_id for item in plan.subtasks}), 2)
        self.assertTrue(plan.validated)

    def test_review_plan_has_dependency(self) -> None:
        plan = make_orchestrator().create_delegation_plan("Review this", "parent", assessment(), {})
        self.assertEqual(plan.subtasks[1].dependency_ids, (plan.subtasks[0].subtask_id,))

    def test_parallel_plan_has_parallel_group(self) -> None:
        plan = make_orchestrator().create_delegation_plan("Parallel review", "parent", assessment(CollaborationMode.PARALLEL), {})
        self.assertEqual(set(plan.parallel_groups[0]), {item.subtask_id for item in plan.subtasks})

    def test_context_is_minimized_and_personal_data_removed(self) -> None:
        plan = make_orchestrator().create_delegation_plan(
            "Review this",
            "parent",
            assessment(),
            {"selected_context": {"active_objective": "safe", "personal_context": "secret", "full_history": "noise"}},
        )
        self.assertEqual(plan.required_context, {"active_objective": "safe"})

    def test_tool_policy_cannot_be_added_to_plan(self) -> None:
        orchestrator = make_orchestrator()
        base = orchestrator.create_delegation_plan("Review this", "parent", assessment(), {})
        invalid = replace(base, tool_policy="unrestricted", validated=False)
        with self.assertRaises(ValueError):
            orchestrator.validate_plan(invalid)

    def test_sequential_dispatch_and_synthesis(self) -> None:
        execution = FakeExecutionManager()
        record = make_orchestrator(execution).coordinate("Review this", "parent", assessment(), {"execution_policy": "local_only", "local_only": True}, True)
        self.assertEqual(record.status, CoordinationStatus.COMPLETED)
        self.assertEqual(record.synthesis, "Synthesized authorized result.")
        self.assertEqual([item.agent_id for item in record.results], ["core-planner", "core-reviewer"])

    def test_provider_policy_is_preserved_for_every_call(self) -> None:
        execution = FakeExecutionManager()
        make_orchestrator(execution).coordinate("Review this", "parent", assessment(), {"execution_policy": "cloud_only", "cloud_only": True}, True)
        self.assertTrue(all(item.metadata["execution_policy"] == "cloud_only" for item in execution.requests))
        self.assertTrue(all(item.metadata["cloud_only"] for item in execution.requests))

    def test_result_normalization_has_provider_and_tool_boundaries(self) -> None:
        record = make_orchestrator().coordinate("Review this", "parent", assessment(), {}, True)
        result = record.results[0]
        self.assertEqual(result.provider_metadata["provider_id"], "local")
        self.assertEqual(result.tool_metadata["tools_executed"], ())
        self.assertEqual(result.status, AgentResultStatus.COMPLETED)

    def test_dependency_failure_blocks_reviewer(self) -> None:
        execution = FakeExecutionManager(fail_agent="core-planner")
        record = make_orchestrator(execution).coordinate("Review this", "parent", assessment(), {}, True)
        self.assertEqual(record.status, CoordinationStatus.FAILED)
        self.assertEqual(record.results[1].status, AgentResultStatus.BLOCKED)

    def test_independent_failure_allows_partial_success(self) -> None:
        execution = FakeExecutionManager(fail_agent="core-reviewer")
        record = make_orchestrator(execution).coordinate("Parallel review", "parent", assessment(CollaborationMode.PARALLEL), {}, True)
        self.assertEqual(record.status, CoordinationStatus.PARTIALLY_COMPLETED)
        self.assertTrue(any(item.success for item in record.results))

    def test_retries_are_bounded(self) -> None:
        execution = FakeExecutionManager(fail_agent="core-reviewer")
        record = make_orchestrator(execution).coordinate("Parallel review", "parent", assessment(CollaborationMode.PARALLEL), {}, True)
        reviewer = next(item for item in record.results if item.agent_id == "core-reviewer")
        self.assertEqual(reviewer.retry_count, 1)
        self.assertEqual(sum(item.metadata["agent_id"] == "core-reviewer" for item in execution.requests), 2)

    def test_timeout_is_not_reported_as_success(self) -> None:
        record = make_orchestrator(TimeoutExecutionManager()).coordinate("Review this", "parent", assessment(), {}, True)
        self.assertEqual(record.results[0].status, AgentResultStatus.TIMED_OUT)
        self.assertEqual(record.status, CoordinationStatus.FAILED)

    def test_conflict_detection_preserves_disagreement(self) -> None:
        record = make_orchestrator().coordinate("Debate this", "parent", assessment(CollaborationMode.DEBATE), {}, True)
        self.assertEqual(len(record.conflicts), 1)
        self.assertFalse(record.conflicts[0].resolved)

    def test_no_results_are_fabricated_when_execution_unavailable(self) -> None:
        orchestrator = make_orchestrator()
        orchestrator.execution_manager = None
        record = orchestrator.coordinate("Review this", "parent", assessment(), {}, True)
        self.assertEqual(record.status, CoordinationStatus.FAILED)
        self.assertEqual(record.results, ())

    def test_cancellation_is_truthful(self) -> None:
        orchestrator = make_orchestrator()
        record = orchestrator.coordinate("Review this", "parent", assessment(), {}, False)
        self.assertTrue(orchestrator.cancel(record.coordination_id))
        self.assertFalse(orchestrator.cancel(record.coordination_id))
        self.assertEqual(orchestrator.store.get(record.coordination_id).status, CoordinationStatus.CANCELLED)  # type: ignore[union-attr]

    def test_limits_reject_excess_subtasks(self) -> None:
        orchestrator = make_orchestrator()
        orchestrator.limits = MultiAgentLimits(maximum_subtasks=1)
        with self.assertRaises(ValueError):
            orchestrator.create_delegation_plan("Review this", "parent", assessment(), {})

    def test_persistence_survives_restart_without_resuming_work(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace = Path(tempdir)
            orchestrator = make_orchestrator(workspace=workspace)
            record = orchestrator.coordinate("Review this", "parent", assessment(), {}, False)
            restored = make_orchestrator(workspace=workspace).store.get(record.coordination_id)
            self.assertIsNotNone(restored)
            self.assertEqual(restored.status, CoordinationStatus.PENDING_APPROVAL)  # type: ignore[union-attr]

    def test_completed_results_are_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tempdir:
            workspace = Path(tempdir)
            record = make_orchestrator(workspace=workspace).coordinate("Review this", "parent", assessment(), {}, True)
            restored = make_orchestrator(workspace=workspace).store.get(record.coordination_id)
            self.assertEqual(len(restored.results), 2)  # type: ignore[union-attr]
            self.assertEqual(restored.synthesis, "Synthesized authorized result.")  # type: ignore[union-attr]

    def test_structured_observability_contains_correlation_ids(self) -> None:
        stream = logging.getLogger("multiagent-test")
        orchestrator = make_orchestrator()
        orchestrator._logger = stream
        with self.assertLogs("multiagent-test", level="INFO") as captured:
            record = orchestrator.coordinate("Review this", "parent-log", assessment(), {}, True)
        output = "\n".join(captured.output)
        self.assertIn("request_id=parent-log", output)
        self.assertIn(f"coordination_id={record.coordination_id}", output)

    def test_commands_are_parsed_and_execute_on_command_path(self) -> None:
        manager = AgentManager(AgentContext(provider_execution_manager=FakeExecutionManager()))
        manager.initialize()
        commands = CommandManager()
        commands.initialize()
        context = ConversationContext(session=ConversationSession(), agent_manager=manager)
        self.assertEqual(commands.parser.parse("multiagent mode off").name, "multiagent mode")
        self.assertIn("mode set to off", commands.execute("multiagent mode off", context).response)
        self.assertIn("mode=off", commands.execute("multiagent status", context).response)
        self.assertIn("maximum_agents", commands.execute("multiagent limits", context).response)

    def test_executive_invokes_multiagent_only_for_assessed_request(self) -> None:
        execution = FakeExecutionManager()
        manager = AgentManager(AgentContext(provider_execution_manager=execution))
        manager.initialize()
        context = JarvisContext(
            request_id="parent-exec",
            agent_manager=manager,
            metadata={"provider_execution_manager": execution},
        )
        response = JarvisController().handle(
            JarvisRequest(content="Use a planner and reviewer to independently review this architecture.", request_id="parent-exec"),
            context,
        )
        self.assertEqual(response.response_type, "multiagent")
        self.assertEqual(response.content, "Synthesized authorized result.")
        self.assertEqual(response.streaming_metadata["parent_request_id"], "parent-exec")

    def test_single_agent_request_does_not_invoke_multiagent_calls(self) -> None:
        execution = FakeExecutionManager()
        manager = AgentManager(AgentContext(provider_execution_manager=execution))
        manager.initialize()
        assessment_result = manager.orchestrator.assess("Say hello.")
        self.assertFalse(assessment_result.requires_multi_agent)
        self.assertEqual(execution.requests, [])


if __name__ == "__main__":
    unittest.main()
