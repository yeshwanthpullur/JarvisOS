"""Tests for the Workflow and Orchestration Engine."""

from __future__ import annotations

import unittest

from jarvis import JarvisCore, JarvisContext, JarvisRequest
from jarvis.jarvis_manager import JarvisManager
from workflow import (
    WorkflowBuilder,
    WorkflowCheckpoint,
    WorkflowContext,
    WorkflowDiagnostics,
    WorkflowDispatcher,
    WorkflowEngine,
    WorkflowExecutor,
    WorkflowHistoryRecord,
    WorkflowHistory,
    WorkflowManager,
    WorkflowMetrics,
    WorkflowRecord,
    WorkflowRecovery,
    WorkflowRegistry,
    WorkflowScheduler,
    WorkflowScheduleMode,
    WorkflowSession,
    WorkflowState,
    WorkflowStatus,
    WorkflowValidator,
    WorkflowStep,
)


def build_definition() -> tuple[WorkflowBuilder, object]:
    builder = WorkflowBuilder()
    definition = builder.create(
        "Research Flow",
        (
            WorkflowStep(name="collect"),
            WorkflowStep(name="analyze", dependencies=("collect",)),
        ),
        workflow_type="research",
    )
    return builder, definition


class WorkflowEngineTests(unittest.TestCase):
    """Workflow engine unit tests."""

    def test_workflow_state_enum_contains_running(self) -> None:
        self.assertEqual(WorkflowState.RUNNING.value, "running")

    def test_workflow_status_enum_contains_healthy(self) -> None:
        self.assertEqual(WorkflowStatus.HEALTHY.value, "healthy")

    def test_context_defaults(self) -> None:
        context = WorkflowContext()
        self.assertTrue(context.workflow_id)

    def test_session_records_ids(self) -> None:
        session = WorkflowSession("w", "e")
        self.assertEqual(session.workflow_id, "w")

    def test_builder_create(self) -> None:
        builder, definition = build_definition()
        self.assertTrue(builder.validate(definition))

    def test_builder_load(self) -> None:
        _, definition = build_definition()
        self.assertEqual(WorkflowBuilder().load(definition).name, "Research Flow")

    def test_builder_clone(self) -> None:
        _, definition = build_definition()
        clone = WorkflowBuilder().clone(definition, workflow_id="clone")
        self.assertEqual(clone.workflow_id, "clone")

    def test_builder_serialize(self) -> None:
        _, definition = build_definition()
        payload = WorkflowBuilder().serialize(definition)
        self.assertEqual(payload["name"], "Research Flow")

    def test_builder_deserialize(self) -> None:
        payload = {"workflow_id": "x", "name": "y", "type": "sequential", "steps": ["a", "b"]}
        definition = WorkflowBuilder().deserialize(payload)
        self.assertEqual(len(definition.steps), 2)

    def test_builder_merge(self) -> None:
        _, definition = build_definition()
        merged = WorkflowBuilder().merge(definition, definition)
        self.assertEqual(len(merged.steps), 4)

    def test_builder_split(self) -> None:
        _, definition = build_definition()
        self.assertEqual(len(WorkflowBuilder().split(definition)), 2)

    def test_builder_template_support(self) -> None:
        self.assertTrue(WorkflowBuilder().template_support()["supported"])

    def test_registry_register_lookup(self) -> None:
        builder, definition = build_definition()
        registry = WorkflowRegistry()
        registry.register(WorkflowRecord(workflow_id=definition.workflow_id, definition=definition))
        self.assertIsNotNone(registry.lookup(definition.workflow_id))

    def test_registry_enable_disable(self) -> None:
        _, definition = build_definition()
        registry = WorkflowRegistry()
        registry.register(WorkflowRecord(workflow_id=definition.workflow_id, definition=definition))
        registry.disable(definition.workflow_id)
        self.assertFalse(registry.lookup(definition.workflow_id).enabled)

    def test_registry_templates(self) -> None:
        _, definition = build_definition()
        registry = WorkflowRegistry()
        registry.register(WorkflowRecord(workflow_id=definition.workflow_id, definition=definition))
        self.assertEqual(len(registry.templates()), 1)

    def test_registry_categories(self) -> None:
        _, definition = build_definition()
        registry = WorkflowRegistry()
        registry.register(WorkflowRecord(workflow_id=definition.workflow_id, definition=definition, category="research"))
        self.assertIn("research", registry.categories())

    def test_registry_versions(self) -> None:
        _, definition = build_definition()
        registry = WorkflowRegistry()
        registry.register(WorkflowRecord(workflow_id=definition.workflow_id, definition=definition, version="1.0"))
        self.assertIn("1.0", registry.versions())

    def test_registry_statistics(self) -> None:
        _, definition = build_definition()
        registry = WorkflowRegistry()
        registry.register(WorkflowRecord(workflow_id=definition.workflow_id, definition=definition))
        self.assertEqual(registry.statistics()["registered_workflows"], 1)

    def test_history_append_and_list(self) -> None:
        history = WorkflowHistory()
        history.append(
            WorkflowHistoryRecord(
                workflow_id="workflow-1",
                execution_id="exec-1",
                steps=("collect",),
                execution_order=("collect",),
                dependencies=(),
                providers=("provider-a",),
                agents=("agent-a",),
                departments=("research",),
            )
        )
        self.assertEqual(len(history.list()), 1)

    def test_history_list_empty(self) -> None:
        self.assertEqual(len(WorkflowHistory().list()), 0)

    def test_metrics_statistics(self) -> None:
        metrics = WorkflowMetrics()
        self.assertEqual(metrics.statistics()["created"], 0)

    def test_checkpoint_create(self) -> None:
        checkpoint = WorkflowCheckpoint("w", "e", "running")
        self.assertEqual(checkpoint.create()["execution_state"], "running")

    def test_recovery_classify_timeout(self) -> None:
        self.assertEqual(WorkflowRecovery().classify_failure("timeout").value, "timeout")

    def test_recovery_plan_records(self) -> None:
        recovery = WorkflowRecovery()
        self.assertTrue(recovery.plan("dependency failed").actions)
        self.assertEqual(recovery.statistics()["recovery_plans"], 1)

    def test_scheduler_schedule(self) -> None:
        schedule = WorkflowScheduler().schedule("workflow-1")
        self.assertEqual(schedule.workflow_id, "workflow-1")

    def test_scheduler_schedule_priority_mode(self) -> None:
        schedule = WorkflowScheduler().schedule("workflow-1", mode=WorkflowScheduleMode.PRIORITY)
        self.assertEqual(schedule.mode, WorkflowScheduleMode.PRIORITY)

    def test_diagnostics_statistics_report(self) -> None:
        _, definition = build_definition()
        registry = WorkflowRegistry()
        registry.register(WorkflowRecord(workflow_id=definition.workflow_id, definition=definition))
        self.assertEqual(WorkflowDiagnostics().statistics_report(registry)["registered_workflows"], 1)

    def test_validator_accepts_valid_definition(self) -> None:
        _, definition = build_definition()
        valid, issues = WorkflowValidator().validate(definition)
        self.assertTrue(valid)
        self.assertEqual(issues, ())

    def test_validator_rejects_missing_steps(self) -> None:
        builder = WorkflowBuilder()
        definition = builder.create("Empty", ())
        valid, issues = WorkflowValidator().validate(definition)
        self.assertFalse(valid)
        self.assertTrue(issues)

    def test_validator_rejects_empty_name(self) -> None:
        definition = WorkflowBuilder().create("", (WorkflowStep(name="one"),))
        valid, _ = WorkflowValidator().validate(definition)
        self.assertFalse(valid)

    def test_executor_execute(self) -> None:
        _, definition = build_definition()
        executor = WorkflowExecutor()
        context = WorkflowContext(workflow_id=definition.workflow_id)
        result = executor.execute(definition, context)
        self.assertEqual(result.workflow_id, definition.workflow_id)

    def test_dispatcher_dispatch_step(self) -> None:
        _, definition = build_definition()
        context = WorkflowContext(workflow_id=definition.workflow_id)
        payload = WorkflowDispatcher().dispatch_step(definition.steps[0], context)
        self.assertEqual(payload["workflow_id"], definition.workflow_id)

    def test_engine_create_workflow(self) -> None:
        _, definition = build_definition()
        engine = WorkflowEngine()
        record = engine.create_workflow(definition)
        self.assertEqual(record.workflow_id, definition.workflow_id)

    def test_engine_validate_workflow(self) -> None:
        _, definition = build_definition()
        self.assertTrue(WorkflowEngine().validate_workflow(definition)[0])

    def test_engine_build_execution_graph(self) -> None:
        _, definition = build_definition()
        graph = WorkflowEngine().build_execution_graph(definition)
        self.assertEqual(graph["workflow_id"], definition.workflow_id)

    def test_engine_create_context(self) -> None:
        context = WorkflowEngine().create_execution_context("workflow-1")
        self.assertEqual(context.workflow_id, "workflow-1")

    def test_engine_create_context_metadata(self) -> None:
        context = WorkflowEngine().create_execution_context("workflow-1", source="test")
        self.assertEqual(context.metadata["source"], "test")

    def test_engine_execute(self) -> None:
        _, definition = build_definition()
        engine = WorkflowEngine()
        result = engine.execute(definition, WorkflowContext(workflow_id=definition.workflow_id))
        self.assertEqual(result.state, WorkflowState.RUNNING)

    def test_engine_summary(self) -> None:
        _, definition = build_definition()
        engine = WorkflowEngine()
        result = engine.execute(definition, WorkflowContext(workflow_id=definition.workflow_id))
        summary = engine.summary(definition, result)
        self.assertEqual(summary.steps, 2)

    def test_engine_registry_records_templates(self) -> None:
        engine = WorkflowEngine()
        _, definition = build_definition()
        engine.create_workflow(definition)
        self.assertEqual(engine.registry.statistics()["registered_workflows"], 1)

    def test_manager_initializes(self) -> None:
        self.assertEqual(WorkflowManager().initialize().overall_workflow_health, "healthy")

    def test_manager_create_workflow(self) -> None:
        _, definition = build_definition()
        manager = WorkflowManager()
        record = manager.create_workflow(definition)
        self.assertEqual(record.workflow_id, definition.workflow_id)

    def test_manager_statistics(self) -> None:
        stats = WorkflowManager().statistics()
        self.assertEqual(stats.workflow_engine_status, "ready")

    def test_jarvis_manager_exposes_workflow(self) -> None:
        manager = JarvisManager()
        self.assertTrue(manager.workflow.initialized)

    def test_jarvis_manager_statistics_include_workflow(self) -> None:
        manager = JarvisManager()
        stats = manager.statistics()
        self.assertEqual(stats.workflow_status, "ready")

    def test_jarvis_core_initializes_with_workflow_manager(self) -> None:
        core = JarvisCore(context=JarvisContext(request_id="test"))
        self.assertTrue(core.manager.workflow.initialized)

    def test_jarvis_request_can_reference_workflow(self) -> None:
        request = JarvisRequest(request_id="req-1", content="workflow")
        self.assertEqual(request.request_id, "req-1")

    def test_workflow_context_serialization_fields(self) -> None:
        context = WorkflowContext()
        self.assertIsNotNone(context.metadata)

    def test_workflow_context_state_defaults(self) -> None:
        context = WorkflowContext()
        self.assertEqual(context.state, WorkflowState.CREATED)

    def test_workflow_session_defaults(self) -> None:
        session = WorkflowSession("a", "b")
        self.assertIsNotNone(session.started_at)

    def test_workflow_session_metadata(self) -> None:
        session = WorkflowSession("a", "b", metadata={"x": 1})
        self.assertEqual(session.metadata["x"], 1)

    def test_workflow_checkpoint_contains_state(self) -> None:
        checkpoint = WorkflowCheckpoint("w", "e", "paused")
        self.assertEqual(checkpoint.execution_state, "paused")

    def test_workflow_checkpoint_create_returns_metadata(self) -> None:
        checkpoint = WorkflowCheckpoint("w", "e", "paused", metadata={"step": 1})
        self.assertEqual(checkpoint.create()["metadata"]["step"], 1)

    def test_workflow_recovery_statistics_empty(self) -> None:
        self.assertEqual(WorkflowRecovery().statistics()["recovery_plans"], 0)

    def test_workflow_recovery_classifies_unknown(self) -> None:
        self.assertEqual(WorkflowRecovery().classify_failure("something else").value, "unknown")

    def test_workflow_registry_unregister(self) -> None:
        _, definition = build_definition()
        registry = WorkflowRegistry()
        registry.register(WorkflowRecord(workflow_id=definition.workflow_id, definition=definition))
        registry.unregister(definition.workflow_id)
        self.assertIsNone(registry.lookup(definition.workflow_id))

    def test_workflow_registry_metadata(self) -> None:
        _, definition = build_definition()
        registry = WorkflowRegistry()
        registry.register(WorkflowRecord(workflow_id=definition.workflow_id, definition=definition, metadata={"k": "v"}))
        self.assertEqual(registry.metadata()[definition.workflow_id]["k"], "v")

    def test_workflow_builder_rejects_empty_name(self) -> None:
        definition = WorkflowBuilder().create("", (WorkflowStep(name="step"),))
        self.assertFalse(WorkflowValidator().validate(definition)[0])

    def test_workflow_builder_rejects_empty_steps(self) -> None:
        definition = WorkflowBuilder().create("Name", ())
        self.assertFalse(WorkflowValidator().validate(definition)[0])

    def test_workflow_engine_registry_templates(self) -> None:
        engine = WorkflowEngine()
        _, definition = build_definition()
        engine.create_workflow(definition)
        self.assertEqual(len(engine.registry.templates()), 1)

    def test_workflow_engine_scheduler_ready(self) -> None:
        self.assertEqual(WorkflowEngine().scheduler.initialized, True)

    def test_workflow_engine_executor_ready(self) -> None:
        self.assertEqual(WorkflowEngine().executor.initialized, True)

    def test_workflow_engine_dispatcher_ready(self) -> None:
        self.assertTrue(WorkflowEngine().dispatcher.initialized)

    def test_workflow_engine_validator_ready(self) -> None:
        self.assertTrue(WorkflowEngine().validator.initialized)

    def test_workflow_manager_has_components(self) -> None:
        manager = WorkflowManager()
        self.assertTrue(manager.registry.initialized)
        self.assertTrue(manager.builder.initialized)
        self.assertTrue(manager.executor.initialized)
        self.assertTrue(manager.dispatcher.initialized)
        self.assertTrue(manager.scheduler.initialized)
        self.assertTrue(manager.recovery.initialized)
        self.assertTrue(manager.diagnostics.initialized)

    def test_workflow_manager_checkpoint_ready(self) -> None:
        self.assertEqual(WorkflowManager().checkpoint.execution_state, "ready")

    def test_workflow_manager_metrics_initial_zero(self) -> None:
        self.assertEqual(WorkflowManager().metrics.created, 0)

    def test_workflow_manager_logger_exists(self) -> None:
        self.assertIsNotNone(WorkflowManager().logger_factory.logger)

    def test_workflow_manager_history_empty(self) -> None:
        self.assertEqual(len(WorkflowManager().history.list()), 0)

    def test_workflow_record_enabled_defaults(self) -> None:
        _, definition = build_definition()
        record = WorkflowRecord(workflow_id=definition.workflow_id, definition=definition)
        self.assertTrue(record.enabled)

    def test_workflow_record_category(self) -> None:
        _, definition = build_definition()
        record = WorkflowRecord(workflow_id=definition.workflow_id, definition=definition, category="research")
        self.assertEqual(record.category, "research")

    def test_workflow_metrics_nested_counts(self) -> None:
        metrics = WorkflowMetrics(parallel_executions=2, sequential_executions=3)
        self.assertEqual(metrics.parallel_executions, 2)
        self.assertEqual(metrics.sequential_executions, 3)

    def test_workflow_metrics_success_rate(self) -> None:
        metrics = WorkflowMetrics(success_rate=0.5)
        self.assertEqual(metrics.success_rate, 0.5)

    def test_workflow_diagnostics_reports_ready(self) -> None:
        self.assertEqual(WorkflowDiagnostics().execution_report()["status"], "ready")

    def test_workflow_diagnostics_dependency_report(self) -> None:
        self.assertEqual(WorkflowDiagnostics().dependency_report()["status"], "ready")

    def test_workflow_diagnostics_recovery_report(self) -> None:
        self.assertEqual(WorkflowDiagnostics().recovery_report(2)["recovery_count"], 2)

    def test_workflow_diagnostics_validation_report(self) -> None:
        self.assertEqual(WorkflowDiagnostics().validation_report()["status"], "ready")

    def test_workflow_step_dependencies(self) -> None:
        step = WorkflowStep(name="analyze", dependencies=("collect",))
        self.assertEqual(step.dependencies, ("collect",))

    def test_workflow_step_metadata(self) -> None:
        step = WorkflowStep(name="analyze", metadata={"kind": "analysis"})
        self.assertEqual(step.metadata["kind"], "analysis")

    def test_workflow_engine_history_record_append(self) -> None:
        history = WorkflowHistory()
        history.append(
            WorkflowHistoryRecord(
                workflow_id="workflow-2",
                execution_id="exec-2",
                steps=("step",),
                execution_order=("step",),
                dependencies=(),
                providers=(),
                agents=(),
                departments=(),
            )
        )
        self.assertEqual(history.list()[0].workflow_id, "workflow-2")

    def test_workflow_scheduler_modes_metadata(self) -> None:
        self.assertEqual(WorkflowScheduler().schedule("w").mode.value, "immediate")

    def test_workflow_engine_record_creation(self) -> None:
        _, definition = build_definition()
        record = WorkflowEngine().create_workflow(definition, category="research")
        self.assertEqual(record.category, "research")

    def test_workflow_engine_graph_contains_steps(self) -> None:
        _, definition = build_definition()
        graph = WorkflowEngine().build_execution_graph(definition)
        self.assertEqual(len(graph["steps"]), 2)

    def test_workflow_executor_result_fields(self) -> None:
        _, definition = build_definition()
        result = WorkflowExecutor().execute(definition, WorkflowContext(workflow_id=definition.workflow_id))
        self.assertEqual(result.results, {})

    def test_workflow_engine_summary_state(self) -> None:
        _, definition = build_definition()
        engine = WorkflowEngine()
        result = engine.execute(definition, WorkflowContext(workflow_id=definition.workflow_id))
        self.assertEqual(engine.summary(definition, result).state, WorkflowState.RUNNING)

    def test_workflow_manager_statistics_active(self) -> None:
        manager = WorkflowManager()
        _, definition = build_definition()
        manager.create_workflow(definition)
        self.assertEqual(manager.statistics().active_workflows, 1)

    def test_workflow_metrics_created_increment(self) -> None:
        metrics = WorkflowMetrics(created=1)
        self.assertEqual(metrics.created, 1)


if __name__ == "__main__":
    unittest.main()
