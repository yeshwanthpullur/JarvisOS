"""Focused verification for roadmap steps 2 through 20."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

from commands import CommandManager
from config.settings import load_settings
from conversation import ConversationContext, ConversationSession
from jarvis.workers.adapters import CodexAdapter, HermesAdapter, MetadataWorkerAdapter, MunderAdapter, OpenCodeAdapter, safe_runner
from jarvis.workers.catalog import DynamicModelRegistry, WorkerRoutePlanner, build_provider_registry
from jarvis.workers.context import ControlledContextStore
from jarvis.workers.models import (
    ContextFragment,
    ContextScope,
    DynamicModelRecord,
    MessageKind,
    ProviderRecord,
    RouteRequest,
    RoutingMode,
    StructuredMessage,
    Task,
    WorkerCapabilities,
    WorkerArtifact,
    WorkerError,
    WorkerErrorCode,
    WorkerRecord,
    WorkerStatus,
    WorkerTask,
    WorkerTaskStatus,
    WorkerResult,
    WorkspaceMode,
    WorkRuntimeLimits,
)
from jarvis.workers.registry import WorkerRegistry
from jarvis.workers.runtime import WorkerRuntime
from jarvis.workers.work import GoalWorkManager, WorkStateStore
from jarvis.workers.worktrees import WorktreeIsolationManager


def successful_runner(command: tuple[str, ...], _timeout: int) -> tuple[int, str, str]:
    if command[-1] == "models":
        return 0, "opencode/model-free\nopencode/paid-preview\n", ""
    return 0, "worker 1.2.3", ""


def failed_runner(_command: tuple[str, ...], _timeout: int) -> tuple[int, str, str]:
    return 1, "", "bounded failure"


def detected(adapter: MetadataWorkerAdapter, executable: str = "worker.cmd") -> MetadataWorkerAdapter:
    adapter._find_executable = lambda: (executable, f"executable:{executable}")  # type: ignore[method-assign]
    return adapter


class WorkerModelTests(unittest.TestCase):
    def test_worker_record_rejects_false_ready_state(self) -> None:
        with self.assertRaises(ValueError):
            WorkerRecord("x", "X", "test", ("x",), status=WorkerStatus.READY)

    def test_worker_task_is_bounded(self) -> None:
        with self.assertRaises(ValueError):
            WorkerTask("x" * 4001, "codex")
        with self.assertRaises(ValueError):
            WorkerTask("safe", "codex", timeout_seconds=0)
        with self.assertRaises(ValueError):
            WorkerTask("safe", "codex", workspace_reference="C:/private/path")

    def test_worker_task_and_result_cover_normalized_contract(self) -> None:
        task = WorkerTask("review", "hermes", workspace_reference="worktrees/task-1", completion_criteria=("tests pass",))
        self.assertIn("main_branch_write", task.denied_capabilities)
        result = WorkerResult(task.task_id, "hermes", WorkerTaskStatus.COMPLETED, response="done", files_changed=("safe.py",), proposed_commands=("pytest",), usage={"tokens": "unknown"})
        self.assertEqual(result.response, "done")

    def test_result_metadata_redacts_secrets_and_private_paths(self) -> None:
        private_path = "C:" + "\\Users\\account\\private.txt"
        result = WorkerResult(
            "task",
            "codex",
            WorkerTaskStatus.COMPLETED,
            files_changed=(private_path,),
            proposed_commands=("tool --" + "api-key=hidden",),
        )
        self.assertEqual(result.files_changed, ("[PRIVATE_PATH]",))
        self.assertNotIn("hidden", result.proposed_commands[0])

    def test_structured_error_codes_are_validated(self) -> None:
        self.assertEqual(WorkerError(WorkerErrorCode.TASK_TIMEOUT, "timed out").code, "task_timeout")
        with self.assertRaises(ValueError):
            WorkerError("invented_error", "no")

    def test_provider_credentials_are_symbolic_only(self) -> None:
        with self.assertRaises(ValueError):
            ProviderRecord("cloud", "cloud", "cloud", "configured", "actual-secret")

    def test_structured_message_types_are_complete(self) -> None:
        expected = {"finding", "question", "request", "artifact", "blocker", "review", "rejection", "approval_request", "completion_claim"}
        self.assertEqual({item.value for item in MessageKind}, expected)

    def test_message_blocks_secrets_and_self_routing(self) -> None:
        with self.assertRaises(ValueError):
            StructuredMessage("s", "t", "a", "b", MessageKind.REQUEST, "api_key=hidden")
        with self.assertRaises(ValueError):
            StructuredMessage("s", "t", "a", "a", MessageKind.REQUEST, "ref:1")


class AdapterContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = detected(MetadataWorkerAdapter("test", "Test", ("test.cmd",), runner=successful_runner))

    def test_detection_and_health_are_truthful(self) -> None:
        detected_record = self.adapter.detect()
        self.assertEqual(detected_record.status, WorkerStatus.DEGRADED)
        self.assertFalse(detected_record.execution_enabled)
        health = self.adapter.health()
        self.assertEqual(health.detected_version, "worker 1.2.3")

    def test_safe_runner_preserves_metadata_lines(self) -> None:
        completed = SimpleNamespace(returncode=0, stdout="worker 1.2.3\nsecondary metadata\n", stderr="")
        with patch("jarvis.workers.adapters.subprocess.run", return_value=completed):
            _code, stdout, _stderr = safe_runner(("worker", "--version"), 2)
        self.assertEqual(stdout.splitlines()[0], "worker 1.2.3")
        self.assertEqual(len(stdout.splitlines()), 2)

    def test_safe_runner_redacts_private_paths(self) -> None:
        private_path = "C:" + "\\Users\\account\\tool"
        completed = SimpleNamespace(returncode=0, stdout=f"worker 1.2.3\n{private_path}\n", stderr="")
        with patch("jarvis.workers.adapters.subprocess.run", return_value=completed):
            _code, stdout, _stderr = safe_runner(("worker", "--version"), 2)
        self.assertNotIn(private_path, stdout)

    def test_codex_login_state_is_checked_without_exposing_output(self) -> None:
        def runner(command: tuple[str, ...], _timeout: int) -> tuple[int, str, str]:
            return (0, "", "Logged in using ChatGPT") if command[-2:] == ("login", "status") else (0, "codex-cli 1.0", "")

        adapter = detected(CodexAdapter(runner), "codex.cmd")
        record = adapter.health()
        self.assertTrue(record.configured)
        self.assertTrue(record.authenticated)
        self.assertNotIn("ChatGPT", record.health_reason)

    def test_missing_worker_is_unavailable_without_install(self) -> None:
        adapter = MetadataWorkerAdapter("missing", "Missing", ("certainly-missing",), runner=failed_runner)
        adapter._find_executable = lambda: ("", "not_detected")  # type: ignore[method-assign]
        self.assertEqual(adapter.detect().status, WorkerStatus.UNAVAILABLE)

    def test_plan_only_start_never_executes_worker(self) -> None:
        result = self.adapter.start_task(WorkerTask("inspect metadata", "test"))
        self.assertEqual(result.status, WorkerTaskStatus.PLANNED)
        self.assertIn("no external process", result.summary)

    def test_approved_execution_is_still_blocked_at_adapter(self) -> None:
        result = self.adapter.start_task(WorkerTask("write code", "test", execution_mode="approved_execution"))
        self.assertEqual(result.status, WorkerTaskStatus.BLOCKED)
        self.assertEqual(result.error.code, "execution_not_authorized")

    def test_full_adapter_lifecycle_is_bounded(self) -> None:
        task = WorkerTask("plan", "test")
        self.adapter.start_task(task)
        self.assertTrue(self.adapter.stream_events(task.task_id))
        self.assertEqual(self.adapter.poll(task.task_id).status, WorkerTaskStatus.PLANNED)
        self.assertIn("opaque", self.adapter.send_context(task.task_id, ("task:1",)).summary)
        self.assertEqual(self.adapter.request_approval(task.task_id, "write").status, WorkerTaskStatus.WAITING)
        self.assertEqual(self.adapter.cancel(task.task_id).status, WorkerTaskStatus.CANCELLED)
        self.assertEqual(self.adapter.resume(task.task_id).status, WorkerTaskStatus.PLANNED)
        self.assertEqual(self.adapter.finish(task.task_id).status, WorkerTaskStatus.COMPLETED)
        self.assertEqual(self.adapter.collect_artifacts(task.task_id), ())

    def test_hermes_is_never_authoritative(self) -> None:
        adapter = detected(HermesAdapter(successful_runner), "hermes.exe")
        record = adapter.health()
        self.assertEqual(record.authority, "external_worker_only")
        self.assertFalse(record.execution_enabled)

    def test_munder_workspace_is_explicitly_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            child = root / "workspace"
            child.mkdir()
            self.assertTrue(MunderAdapter.validate_workspace(child, root))
            self.assertFalse(MunderAdapter.validate_workspace(root.parent, root))


class WorkerRegistryTests(unittest.TestCase):
    def test_duplicate_worker_rejected(self) -> None:
        adapter = MetadataWorkerAdapter("x", "X", ("x",))
        with self.assertRaises(ValueError):
            WorkerRegistry((adapter, adapter))

    def test_registry_inventory_is_machine_readable_and_safe(self) -> None:
        adapter = detected(MetadataWorkerAdapter("x", "X", ("x.cmd",), runner=successful_runner))
        registry = WorkerRegistry((adapter,))
        registry.refresh(health=True)
        payload = json.loads(registry.inventory_json())
        self.assertEqual(payload["authority"], "metadata_and_plan_only")
        self.assertEqual(payload["workers"][0]["worker_id"], "x")
        self.assertNotIn("C:\\Users", registry.inventory_json())

    def test_registry_validation_preserves_authority(self) -> None:
        adapter = detected(MetadataWorkerAdapter("x", "X", ("x.cmd",), runner=successful_runner))
        registry = WorkerRegistry((adapter,))
        self.assertEqual(registry.validate(), ())
        self.assertEqual(registry.summary()["execution_enabled"], 0)

    def test_partial_lookup_does_not_hide_other_registered_workers(self) -> None:
        first = MetadataWorkerAdapter("first", "First", ("first",))
        second = MetadataWorkerAdapter("second", "Second", ("second",))
        first._find_executable = lambda: ("first.cmd", "executable:first")  # type: ignore[method-assign]
        second._find_executable = lambda: ("", "not_detected")  # type: ignore[method-assign]
        registry = WorkerRegistry((first, second))
        registry.get("first")
        self.assertEqual(registry.summary()["registered"], 2)


class WorkerRuntimeIntegrationTests(unittest.TestCase):
    def test_command_uses_executive_worker_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = WorkerRuntime(Path(directory))
            runtime.set_ollama_health(True)
            manager = SimpleNamespace(worker_runtime=runtime)
            context = ConversationContext(ConversationSession(), jarvis_core=SimpleNamespace(manager=manager))
            commands = CommandManager()
            commands.initialize()
            response = commands.execute("worker route coding local_only", context)
        self.assertIn("provider=ollama", response.response)

    def test_cloud_routes_are_disabled_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = WorkerRuntime(Path(directory))
            runtime.models.register(DynamicModelRecord("opencode/free", "opencode", free=True, cost_class="free"))
            decision = runtime.route(RouteRequest("coding", RoutingMode.NORMAL_HYBRID))
        self.assertEqual(decision.status, "unavailable")
        self.assertIn("disabled", decision.reason)

    def test_worker_settings_load_safe_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(config_file=Path(directory) / "missing.yaml", env_file=Path(directory) / "missing.env")
        self.assertEqual(settings.workers.default_mode, "plan_only")
        self.assertEqual(settings.workers.default_routing_mode, "local_only")
        self.assertFalse(settings.workers.allow_cloud_routes)
        self.assertTrue(settings.workers.require_approval_for_writes)
        self.assertFalse(settings.workers.worktree_auto_merge)


class DynamicModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = detected(OpenCodeAdapter(successful_runner), "opencode.cmd")

    def test_refresh_discovers_models_and_free_metadata(self) -> None:
        registry = DynamicModelRegistry()
        models = registry.refresh_opencode(self.adapter)
        self.assertEqual(len(models), 2)
        free = registry.get("opencode/model-free")
        self.assertTrue(free.free)
        self.assertFalse(free.exact_price_known)

    def test_free_classification_does_not_guess_from_prefix(self) -> None:
        self.adapter.runner = lambda command, timeout: (0, "opencode/freebird-paid\n", "")
        model = DynamicModelRegistry().refresh_opencode(self.adapter)[0]
        self.assertIsNone(model.free)

    def test_ox_alpha_remains_unresolved_without_exact_discovery(self) -> None:
        registry = DynamicModelRegistry()
        registry.refresh_opencode(self.adapter)
        alias = registry.alias("ox-alpha")
        self.assertEqual(alias.status, "unresolved")
        self.assertIsNone(alias.target_model_id)

    def test_removed_model_becomes_unavailable(self) -> None:
        registry = DynamicModelRegistry()
        registry.refresh_opencode(self.adapter)
        self.adapter.runner = lambda command, timeout: (0, "opencode/model-free\n", "")
        registry.refresh_opencode(self.adapter)
        self.assertEqual(registry.get("opencode/paid-preview").status, "unavailable")

    def test_temporary_model_expiration_is_safe(self) -> None:
        registry = DynamicModelRegistry()
        registry.register(DynamicModelRecord("opencode/temp", "opencode", temporary=True, expires_at="2000-01-01T00:00:00+00:00"))
        self.assertEqual(registry.expire_temporary(), ("opencode/temp",))
        self.assertEqual(registry.get("opencode/temp").status, "unavailable")

    def test_provider_catalog_has_local_and_safe_cloud_references(self) -> None:
        providers = build_provider_registry(ollama_detected=True)
        self.assertTrue(providers.get("ollama").enabled)
        for provider_id in ("openrouter", "tokenrouter", "zenmux", "openai", "anthropic", "google", "deepseek", "qwen"):
            self.assertFalse(providers.get(provider_id).enabled)


class RoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.models = DynamicModelRegistry()
        self.models.register(DynamicModelRecord("opencode/free", "opencode", free=True, cost_class="free"))
        self.router = WorkerRoutePlanner(self.models)
        self.workers = (
            WorkerRecord("codex", "Codex", "test", ("codex.cmd",), WorkerStatus.DEGRADED, capabilities=WorkerCapabilities(independent_review=True)),
            WorkerRecord("hermes", "Hermes", "test", ("hermes.exe",), WorkerStatus.DEGRADED, capabilities=WorkerCapabilities(independent_review=True)),
        )

    def test_local_provider_is_first(self) -> None:
        route = self.router.select(RouteRequest("coding", RoutingMode.LOCAL_ONLY), self.workers, ollama_ready=True)
        self.assertEqual(route.provider_id, "ollama")

    def test_local_only_fails_without_local_model(self) -> None:
        route = self.router.select(RouteRequest("coding", RoutingMode.LOCAL_ONLY), self.workers, ollama_ready=False)
        self.assertEqual(route.status, "unavailable")

    def test_hybrid_can_select_discovered_free_model(self) -> None:
        route = self.router.select(RouteRequest("coding", RoutingMode.NORMAL_HYBRID), self.workers, ollama_ready=False)
        self.assertEqual(route.model_id, "opencode/free")

    def test_independent_reviewer_is_different(self) -> None:
        route = self.router.select(RouteRequest("coding", independent_review=True), self.workers, ollama_ready=True)
        self.assertNotEqual(route.worker_id, route.reviewer_worker_id)

    def test_write_route_requires_approval(self) -> None:
        route = self.router.select(RouteRequest("coding", requires_repository_write=True), self.workers, ollama_ready=True)
        self.assertTrue(route.approval_required)
        self.assertEqual(route.execution_mode, "plan_only")

    def test_high_risk_route_requires_approval(self) -> None:
        route = self.router.select(RouteRequest("coding", risk_level="high"), self.workers, ollama_ready=True)
        self.assertTrue(route.approval_required)

    def test_assignment_uses_bounded_specialists(self) -> None:
        workers = self.workers + (
            WorkerRecord("aider", "Aider", "test", ("aider",), WorkerStatus.DEGRADED),
        )
        self.assertEqual(self.router.select(RouteRequest("general delegated work"), workers, ollama_ready=True).worker_id, "hermes")
        self.assertEqual(self.router.select(RouteRequest("small edit"), workers, ollama_ready=True).worker_id, "aider")


class WorkManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = GoalWorkManager(WorkRuntimeLimits(max_parallel_tasks=2))

    def test_goal_and_task_dag(self) -> None:
        goal = self.manager.create_goal("ship safely", ("tests pass",))
        first = Task("inspect", "codex", task_id="first")
        second = Task("review", "hermes", ("first",), task_id="second")
        self.manager.add_task(first, goal.goal_id)
        self.manager.add_task(second, goal.goal_id)
        self.assertEqual([item.task_id for item in self.manager.ready_tasks(goal.goal_id)], ["first"])
        self.manager.mark("first", WorkerTaskStatus.RUNNING)
        self.manager.mark("first", WorkerTaskStatus.COMPLETED)
        self.assertEqual([item.task_id for item in self.manager.ready_tasks(goal.goal_id)], ["second"])

    def test_cycle_and_missing_dependency_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.manager.add_task(Task("bad", "codex", ("missing",), task_id="bad"))
        self.manager.add_task(Task("a", "codex", task_id="a"), "s")
        self.manager.tasks["a"] = replace(self.manager.tasks["a"], dependencies=("b",))
        self.manager.tasks["b"] = Task("b", "codex", ("a",), task_id="b")
        self.manager.sessions["s"].add("b")
        with self.assertRaises(ValueError):
            self.manager.validate_dag("s")

    def test_parallelism_is_bounded(self) -> None:
        for index in range(4):
            self.manager.add_task(Task(str(index), "codex", task_id=f"t{index}"))
        self.assertEqual(len(self.manager.ready_tasks()), 2)

    def test_cancel_and_resume(self) -> None:
        self.manager.add_task(Task("x", "codex", task_id="x"))
        self.assertTrue(self.manager.cancel("x"))
        self.assertTrue(self.manager.resume("x"))
        self.assertEqual(self.manager.tasks["x"].status, WorkerTaskStatus.QUEUED)

    def test_timeout_is_bounded(self) -> None:
        self.manager.add_task(Task("x", "codex", task_id="x", timeout_seconds=1))
        self.manager.mark("x", WorkerTaskStatus.RUNNING)
        self.manager.started_at["x"] = datetime.now(UTC) - timedelta(seconds=2)
        self.assertEqual(self.manager.expire_timeouts(), ("x",))

    def test_structured_messages_are_session_scoped(self) -> None:
        self.manager.add_task(Task("x", "codex", task_id="x"), "s")
        message = StructuredMessage("s", "x", "codex", "prime_agent", MessageKind.FINDING, "evidence:1")
        self.assertEqual(self.manager.send(message), message)
        with self.assertRaises(ValueError):
            self.manager.send(replace(message, session_id="other", message_id="other"))

    def test_completion_claim_requires_evidence(self) -> None:
        self.manager.add_task(Task("x", "codex", task_id="x"), "s")
        with self.assertRaises(ValueError):
            self.manager.completion_claim("s", "x", "codex", ())

    def test_persistent_status_omits_objective(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            manager = GoalWorkManager(store=WorkStateStore(path))
            manager.create_goal("private objective", ("done",))
            manager.add_task(Task("private task", "codex", task_id="x"))
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("private objective", text)
            self.assertNotIn("private task", text)
            restored = GoalWorkManager(store=WorkStateStore(path))
            self.assertEqual(restored.tasks["x"].status, WorkerTaskStatus.QUEUED)
            self.assertEqual(restored.tasks["x"].title, "[retained metadata]")


class ContextAndWorktreeTests(unittest.TestCase):
    def test_context_scopes_and_personal_data_are_separated(self) -> None:
        store = ControlledContextStore()
        store.add("c", ContextFragment(ContextScope.TASK, "task:1", "user_request"))
        store.add("c", ContextFragment(ContextScope.PERSONAL_REFERENCE, "memory:1", "memory_authority", contains_personal_data=True))
        selected = store.select("c", scopes=(ContextScope.TASK, ContextScope.PERSONAL_REFERENCE))
        self.assertEqual([item.reference for item in selected], ["task:1"])
        self.assertEqual(len(store.select("c", scopes=(ContextScope.PERSONAL_REFERENCE,), allow_personal=True)), 1)

    def test_context_budget_is_enforced(self) -> None:
        store = ControlledContextStore(max_chars=1000)
        store.add("c", ContextFragment(ContextScope.TASK, "x", "p", char_budget=900))
        with self.assertRaises(ValueError):
            store.add("c", ContextFragment(ContextScope.TASK, "y", "p", char_budget=200))

    def test_worktree_plan_uses_safe_branch_and_never_auto_merges(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manager = WorktreeIsolationManager(root, root / "worktrees")
            plan = manager.plan("T 1", "Fix parser")
            self.assertTrue(plan.branch_name.startswith("jarvis/task-"))
            self.assertFalse(plan.auto_merge)
            self.assertEqual(manager.create("T 1").status, "approval_required")
            self.assertEqual(manager.map_artifact("T 1", "reports/result.json").artifact_refs, ("reports/result.json",))

    def test_simulated_parallel_results_and_failures_are_isolated(self) -> None:
        manager = GoalWorkManager(WorkRuntimeLimits(max_parallel_tasks=2))
        manager.add_task(Task("one", "good", task_id="one", parallel_safe=True), "s")
        manager.add_task(Task("two", "bad", task_id="two", parallel_safe=True), "s")
        from jarvis.workers.models import Result
        results = manager.simulate_parallel("s", {
            "good": lambda task: Result(task.task_id, WorkerTaskStatus.COMPLETED, summary="ok"),
            "bad": lambda task: (_ for _ in ()).throw(RuntimeError("boom")),
        })
        self.assertEqual({item.status for item in results}, {WorkerTaskStatus.COMPLETED, WorkerTaskStatus.FAILED})

    def test_private_context_reference_is_rejected(self) -> None:
        private_path = "C:" + "\\Users\\account\\memory.txt"
        with self.assertRaises(ValueError):
            ContextFragment(ContextScope.TASK, private_path, "user_request")


class WorkerCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.runtime = WorkerRuntime(Path(self.temp.name))
        adapter = detected(MetadataWorkerAdapter("codex", "Codex", ("codex.cmd",), runner=successful_runner))
        self.runtime.registry = WorkerRegistry((adapter,))
        self.context = ConversationContext(session=ConversationSession(), metadata={"worker_runtime": self.runtime})
        self.commands = CommandManager()
        self.commands.initialize()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_worker_cli_commands_are_registered_and_bounded(self) -> None:
        commands = (
            "worker status", "worker list", "worker show codex", "worker health codex",
            "worker inventory", "worker models", "worker providers", "worker route coding",
            "worker task-plan codex inspect", "work status", "work plan inspect repository",
            "work context default", "work messages",
        )
        for command in commands:
            output = self.commands.execute(command, self.context).response
            self.assertTrue(output, command)
            self.assertLess(len(output), 12_001, command)
            self.assertNotIn("api_key=", output.lower())
            self.assertNotIn("C:\\Users", output)

    def test_project_status_includes_worker_foundation(self) -> None:
        output = self.commands.execute("project status", self.context).response
        self.assertIn("workers:", output)


if __name__ == "__main__":
    unittest.main()
