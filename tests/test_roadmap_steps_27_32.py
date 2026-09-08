from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from jarvis.control_room import ControlRoomRuntime
from jarvis.workers.assurance import evidence_integrity
from jarvis.workers.assurance_models import EvidenceRecord, EvidenceType
from jarvis.workers.benchmarks import MUNDER_EVALUATION, OrchestrationBenchmarks
from jarvis.workers.models import Task, WorkerTaskStatus
from jarvis.workers.runtime import WorkerRuntime


class BenchmarkTests(unittest.TestCase):
    def test_small_real_project_exercises_isolated_verified_pipeline(self) -> None:
        result = OrchestrationBenchmarks.small_project()
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.tasks, 2)
        self.assertGreaterEqual(result.evidence_count, 3)
        self.assertIn("ready", result.outcome)
        self.assertIn("automatic_merge=False", result.outcome)

    def test_gesture_reel_benchmark_separates_validation_layers(self) -> None:
        result = OrchestrationBenchmarks.gesture_reel()
        layers = dict(result.validation_layers)
        self.assertEqual(result.status, "degraded")
        self.assertEqual(layers["physical_device_validation"], "not_run_no_device")
        self.assertEqual(layers["real_app_platform_validation"], "not_run_no_authenticated_platform")
        self.assertTrue(result.weaknesses)

    def test_munder_is_optional_and_unsafe_spawning_is_rejected(self) -> None:
        assessment = {name: category for name, category, _ in MUNDER_EVALUATION}
        self.assertEqual(assessment["agent_spawning"], "UNSAFE/INCOMPATIBLE")
        self.assertEqual(assessment["workspace_isolation"], "REIMPLEMENT_NATIVELY")
        self.assertNotIn("REQUIRED_DEPENDENCY", assessment.values())

    def test_worker_orchestration_remains_available_without_munder(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = WorkerRuntime(Path(directory))
            runtime.registry._records.pop("munder", None)
            self.assertEqual(runtime.status()["authority"], "plan_route_diagnose_only")
            self.assertEqual(runtime.work.status()["authority"], "coordination_only")

    def test_munder_failure_cannot_override_jarvis_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = WorkerRuntime(Path(directory))
            record = runtime.registry.get("munder")
            if record is not None:
                self.assertEqual(record.authority, "external_worker_only")
            self.assertFalse(runtime.status()["approval_bypass"])


class ControlRoomTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.workers = WorkerRuntime(Path(self.temp.name))
        self.control = ControlRoomRuntime(self.workers, max_events=20)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_backend_reads_are_bounded_and_secret_free(self) -> None:
        for index in range(120):
            if index < self.workers.limits.max_tasks:
                self.workers.work.add_task(Task(f"Task {index}", "worker", task_id=f"task-{index}"), "session")
            self.control.emit("TaskCreated", f"Task {index} created", "queued", task_id=f"task-{index}")
        snapshot = self.control.snapshot(limit=10)
        self.assertEqual(len(snapshot["tasks"]), 10)
        self.assertEqual(len(snapshot["activity"]), 10)
        text = str(snapshot)
        self.assertNotIn("api_key=", text.lower())
        self.assertNotIn(str(Path.home()), text)
        self.assertFalse(snapshot["security"]["shell"])

    def test_events_and_pause_resume_cancel_actions(self) -> None:
        self.workers.work.add_task(Task("Controlled task", "worker", task_id="task"), "session")
        self.workers.work.mark("task", WorkerTaskStatus.RUNNING)
        self.assertEqual(self.control.action("pause_task", task_id="task")["status"], "waiting")
        self.assertEqual(self.control.action("resume_task", task_id="task")["status"], "running")
        self.assertEqual(self.control.action("cancel_task", task_id="task")["status"], "cancelled")
        self.assertEqual([event.event_type for event in self.control.events], ["TaskPaused", "TaskResumed", "TaskCancelled"])

    def test_unknown_task_and_unauthorized_approval_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown_task"):
            self.control.action("cancel_task", task_id="missing")
        self.workers.work.add_task(Task("Approval task", "worker", task_id="task"), "session")
        with self.assertRaisesRegex(ValueError, "authorization_required"):
            self.control.action("approve_step", task_id="task", approval_ref="missing")

    def test_retry_is_bounded(self) -> None:
        self.workers.work.add_task(Task("Retry task", "worker", task_id="task", status=WorkerTaskStatus.FAILED, max_retries=1), "session")
        result = self.control.action("request_retry", task_id="task")
        self.assertEqual(result["status"], "retrying")
        self.assertEqual(self.workers.work.tasks["task"].retry_count, 1)

    def test_evidence_inspection_returns_only_bounded_metadata(self) -> None:
        summary = "Focused validation passed."
        reference = "tests:control-room"
        item = self.workers.assurance.evidence.add(EvidenceRecord("task", "run", EvidenceType.TEST_RESULT, "pytest", summary, reference, validated=True, integrity=evidence_integrity(summary, reference)))
        result = self.control.action("inspect_evidence", evidence_id=item.evidence_id)
        self.assertEqual(result["evidence"]["summary"], summary)
        self.assertNotIn("safe_reference", result["evidence"])

    def test_local_ui_contains_required_control_room_views(self) -> None:
        root = Path(__file__).resolve().parents[1]
        html = (root / "desktop" / "index.html").read_text(encoding="utf-8")
        script = (root / "desktop" / "app.js").read_text(encoding="utf-8")
        for name in ("board", "dag", "workers", "evidence", "approvals", "providers", "activity"):
            self.assertIn(f'data-control-tab="{name}"', html)
        self.assertIn('/api/control-room', script)
        self.assertNotIn("arbitrary shell", html.lower())
        self.assertNotIn("auto-merge", html.lower())


if __name__ == "__main__":
    unittest.main()
