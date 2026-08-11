"""Focused Prompt 82 workflow runtime tests."""

from __future__ import annotations

import unittest

from config import load_settings
from jarvis.jarvis_manager import JarvisManager
from workflow import (
    RuntimeWorkflowStep,
    WorkflowDependency,
    WorkflowDependencyType,
    WorkflowExecutionMode,
    WorkflowLimits,
    WorkflowRuntime,
    WorkflowRuntimeState,
    WorkflowStepState,
    render_workflow_command,
)


def make_runtime() -> tuple[WorkflowRuntime, object]:
    runtime = WorkflowRuntime()
    first = RuntimeWorkflowStep("plan", "planning", owner_agent="prime")
    second = RuntimeWorkflowStep("review", "review", dependencies=(WorkflowDependency("plan"),))
    return runtime, runtime.create("Review architecture", (first, second))


class WorkflowModelTests(unittest.TestCase):
    def test_safe_limits(self) -> None:
        self.assertEqual(WorkflowLimits().max_parallel_steps, 2)

    def test_limits_reject_unbounded_retry(self) -> None:
        with self.assertRaises(ValueError):
            WorkflowLimits(max_retry_count=6)

    def test_workflow_is_planned(self) -> None:
        _, workflow = make_runtime()
        self.assertEqual(workflow.state, WorkflowRuntimeState.PLANNED)

    def test_duplicate_steps_rejected(self) -> None:
        runtime = WorkflowRuntime()
        with self.assertRaisesRegex(ValueError, "duplicate"):
            runtime.create("x", (RuntimeWorkflowStep("a", "x"), RuntimeWorkflowStep("a", "x")))

    def test_unknown_dependency_rejected(self) -> None:
        runtime = WorkflowRuntime()
        with self.assertRaisesRegex(ValueError, "unknown"):
            runtime.create("x", (RuntimeWorkflowStep("a", "x", dependencies=(WorkflowDependency("missing"),)),))

    def test_cycle_rejected(self) -> None:
        runtime = WorkflowRuntime()
        steps = (RuntimeWorkflowStep("a", "x", dependencies=(WorkflowDependency("b"),)), RuntimeWorkflowStep("b", "x", dependencies=(WorkflowDependency("a"),)))
        with self.assertRaisesRegex(ValueError, "cycle"):
            runtime.create("x", steps)

    def test_dependency_types_complete(self) -> None:
        self.assertEqual(len(WorkflowDependencyType), 8)


class WorkflowExecutionTests(unittest.TestCase):
    def test_sequential_dependency_order(self) -> None:
        runtime, workflow = make_runtime()
        runtime.start(workflow.workflow_id)
        self.assertEqual([step.step_id for step in runtime.ready_steps(workflow.workflow_id)], ["plan"])
        runtime.run_step(workflow.workflow_id, "plan")
        self.assertEqual([step.step_id for step in runtime.ready_steps(workflow.workflow_id)], ["review"])

    def test_completion(self) -> None:
        runtime, workflow = make_runtime()
        runtime.start(workflow.workflow_id)
        runtime.run_step(workflow.workflow_id, "plan")
        runtime.run_step(workflow.workflow_id, "review")
        self.assertEqual(workflow.state, WorkflowRuntimeState.COMPLETED)

    def test_parallel_steps_are_bounded(self) -> None:
        runtime = WorkflowRuntime(WorkflowLimits(max_active=3, max_parallel_steps=2))
        workflow = runtime.create("parallel", tuple(RuntimeWorkflowStep(str(index), "x") for index in range(3)), workflow_type="parallel")
        runtime.start(workflow.workflow_id)
        self.assertEqual(len(runtime.ready_steps(workflow.workflow_id)), 2)

    def test_background_execution_is_disabled(self) -> None:
        runtime = WorkflowRuntime()
        workflow = runtime.create("background", (RuntimeWorkflowStep("one", "x"),), mode=WorkflowExecutionMode.BACKGROUND)
        with self.assertRaisesRegex(ValueError, "background"):
            runtime.start(workflow.workflow_id)

    def test_approval_is_propagated(self) -> None:
        runtime = WorkflowRuntime()
        workflow = runtime.create("write", (RuntimeWorkflowStep("write", "file_write", approval_required=True, broker_required=True),))
        runtime.start(workflow.workflow_id)
        runtime.run_step(workflow.workflow_id, "write")
        self.assertEqual(workflow.state, WorkflowRuntimeState.WAITING)

    def test_broker_result_is_authoritative(self) -> None:
        runtime = WorkflowRuntime()
        workflow = runtime.create("write", (RuntimeWorkflowStep("write", "file_write", broker_required=True),))
        runtime.start(workflow.workflow_id)
        runtime.run_step(workflow.workflow_id, "write", broker=lambda _: {"status": "blocked", "error": "policy_denied"})
        self.assertEqual(workflow.state, WorkflowRuntimeState.FAILED)

    def test_retry_is_bounded(self) -> None:
        runtime = WorkflowRuntime()
        workflow = runtime.create("retry", (RuntimeWorkflowStep("one", "x", maximum_retries=1),))
        runtime.start(workflow.workflow_id)
        runtime.run_step(workflow.workflow_id, "one", broker=lambda _: {"status": "failed"})
        self.assertEqual(workflow.steps[0].status, WorkflowStepState.PENDING)
        runtime.run_step(workflow.workflow_id, "one", broker=lambda _: {"status": "failed"})
        self.assertEqual(workflow.state, WorkflowRuntimeState.FAILED)

    def test_step_timeout_checkpoints(self) -> None:
        runtime = WorkflowRuntime()
        workflow = runtime.create("timeout", (RuntimeWorkflowStep("one", "x", timeout_seconds=1),))
        runtime.start(workflow.workflow_id)
        runtime.run_step(workflow.workflow_id, "one", elapsed_seconds=2)
        self.assertEqual(workflow.state, WorkflowRuntimeState.TIMED_OUT)
        self.assertTrue(runtime.checkpoints)


class WorkflowCheckpointTests(unittest.TestCase):
    def test_checkpoint_and_restore(self) -> None:
        runtime, workflow = make_runtime()
        runtime.start(workflow.workflow_id)
        runtime.run_step(workflow.workflow_id, "plan")
        checkpoint = list(runtime.checkpoints.values())[-1]
        workflow.completed_steps.clear()
        restored = runtime.restore(checkpoint.checkpoint_id)
        self.assertEqual(restored.completed_steps, ["plan"])

    def test_version_mismatch_is_rejected(self) -> None:
        runtime, workflow = make_runtime()
        checkpoint = runtime.checkpoint(workflow.workflow_id)
        with self.assertRaisesRegex(ValueError, "version"):
            runtime.restore(checkpoint.checkpoint_id, workflow_version="2.0")

    def test_corrupt_checkpoint_is_rejected(self) -> None:
        runtime, _ = make_runtime()
        with self.assertRaisesRegex(ValueError, "corrupt"):
            runtime.restore("missing")

    def test_recovery_pauses_at_safe_boundary(self) -> None:
        runtime, workflow = make_runtime()
        checkpoint = runtime.checkpoint(workflow.workflow_id)
        recovered = runtime.recover(checkpoint.checkpoint_id)
        self.assertEqual(recovered.state, WorkflowRuntimeState.PAUSED)
        self.assertEqual(recovered.mode, WorkflowExecutionMode.RECOVERY)

    def test_pause_resume_cycles(self) -> None:
        runtime, workflow = make_runtime()
        runtime.start(workflow.workflow_id)
        for _ in range(2):
            runtime.pause(workflow.workflow_id)
            self.assertEqual(workflow.state, WorkflowRuntimeState.PAUSED)
            runtime.resume(workflow.workflow_id)
        self.assertEqual(workflow.state, WorkflowRuntimeState.RUNNING)

    def test_cancel_clears_pending_work(self) -> None:
        runtime, workflow = make_runtime()
        runtime.cancel(workflow.workflow_id)
        self.assertTrue(all(step.status is WorkflowStepState.CANCELLED for step in workflow.steps))


class WorkflowArtifactSecurityTests(unittest.TestCase):
    def test_artifact_is_metadata_only(self) -> None:
        runtime, workflow = make_runtime()
        artifact = runtime.add_artifact(workflow.workflow_id, "report", "bounded summary")
        self.assertEqual(artifact.storage_class, "metadata_only")

    def test_cleanup_is_dry_run(self) -> None:
        runtime, workflow = make_runtime()
        runtime.add_artifact(workflow.workflow_id, "report", "temporary")
        self.assertTrue(runtime.cleanup_plan()["dry_run"])

    def test_secret_is_redacted_from_request(self) -> None:
        runtime = WorkflowRuntime()
        workflow = runtime.create("token=abc123", (RuntimeWorkflowStep("one", "x"),))
        self.assertNotIn("abc123", workflow.initiating_request)

    def test_secret_metadata_is_removed(self) -> None:
        step = RuntimeWorkflowStep("one", "x", inputs={"api_key": "bad", "safe": "ok"})
        self.assertNotIn("api_key", step.inputs)

    def test_absolute_path_is_reduced(self) -> None:
        runtime = WorkflowRuntime()
        workflow = runtime.create("C:\\Users\\Private\\secret.txt", (RuntimeWorkflowStep("one", "x"),))
        self.assertNotIn("C:/Users", workflow.initiating_request)

    def test_checkpoint_contains_references_not_payload(self) -> None:
        runtime, workflow = make_runtime()
        checkpoint = runtime.checkpoint(workflow.workflow_id)
        self.assertEqual(checkpoint.context_reference, f"workflow:{workflow.workflow_id}")
        self.assertFalse(hasattr(checkpoint, "credentials"))

    def test_serialization_has_no_secret(self) -> None:
        runtime, _ = make_runtime()
        self.assertTrue(runtime.validate_serializable())


class WorkflowCliConfigTests(unittest.TestCase):
    def test_status_and_health(self) -> None:
        runtime = WorkflowRuntime()
        self.assertIn("execution_authority=False", render_workflow_command(runtime, "workflow status", ()))
        self.assertIn("coordination_only", render_workflow_command(runtime, "workflow health", ()))

    def test_simulation_has_no_side_effects(self) -> None:
        output = render_workflow_command(WorkflowRuntime(), "workflow simulate", ("test",))
        self.assertIn("side_effects=False", output)

    def test_bounded_events_and_metrics(self) -> None:
        runtime, workflow = make_runtime()
        self.assertLessEqual(len(render_workflow_command(runtime, "workflow events", (workflow.workflow_id,))), 4000)
        self.assertIn("created=1", render_workflow_command(runtime, "workflow metrics", ()))

    def test_missing_workflow_fails_safely(self) -> None:
        self.assertIn("workflow_not_found", render_workflow_command(WorkflowRuntime(), "workflow show", ("missing",)))

    def test_configuration_defaults(self) -> None:
        settings = load_settings()
        self.assertTrue(settings.workflow.enabled)
        self.assertTrue(settings.workflow.enable_audit)
        self.assertLessEqual(settings.workflow.max_retry_count, 5)

    def test_prime_uses_authoritative_workflow_runtime(self) -> None:
        manager = JarvisManager()
        self.assertIs(manager.prime_agent.workflow_runtime, manager.workflow.runtime)


if __name__ == "__main__":
    unittest.main()
