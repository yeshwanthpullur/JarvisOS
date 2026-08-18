"""Prompt 93-98 modality, coding, automation, connector, and observability tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from commands import CommandManager
from jarvis.phase6 import build_tool_environment_registry
from jarvis.phase6.automation import LocalAction, LocalAutomationControlPlane
from jarvis.phase6.coding_tools import ExternalCodingControlPlane
from jarvis.phase6.connectors import ConnectorRegistry
from jarvis.phase6.modalities import VisionControlPlane, VoiceAdapterRouter
from jarvis.phase6.observability import ObservabilityRuntime
from jarvis.phase6.runtime import Phase6Runtime


class ModalityTests(unittest.TestCase):
    def test_voice_never_enables_hidden_capture(self) -> None:
        status = VoiceAdapterRouter(build_tool_environment_registry()).status()
        self.assertFalse(status["wake_enabled"])
        self.assertFalse(status["continuous_listening"])
        self.assertFalse(status["raw_audio_retained"])
        self.assertFalse(status["cloud_upload"])

    def test_tts_has_text_only_safe_local_fallback(self) -> None:
        route = VoiceAdapterRouter(build_tool_environment_registry()).tts()
        self.assertIn(route.selected, {"piper", "windows_sapi"})
        self.assertTrue(route.local_only)

    def test_visual_input_is_untrusted_and_not_retained(self) -> None:
        with TemporaryDirectory() as folder:
            image = Path(folder) / "sample.png"; image.write_bytes(b"\x89PNG\r\n\x1a\n")
            result = VisionControlPlane().inspect(str(image))
            self.assertFalse(result.trusted)
            self.assertFalse(result.retained)
            self.assertEqual(result.status, "ready_for_explicit_analysis")

    def test_camera_is_blocked_by_default(self) -> None:
        runtime = VisionControlPlane()
        self.assertFalse(runtime.status()["camera_enabled"])
        self.assertIn("blocked", runtime.camera_start().lower())


class CodingToolTests(unittest.TestCase):
    def test_external_tools_are_plan_only(self) -> None:
        with TemporaryDirectory() as folder:
            runtime = ExternalCodingControlPlane(Path(folder), build_tool_environment_registry())
            task = runtime.plan("Fix a harmless bug")
            self.assertEqual(task.mode, "plan_only")
            self.assertFalse(task.write_allowed)
            self.assertFalse(task.shell_allowed)
            self.assertFalse(task.network_allowed)
            self.assertEqual(runtime.apply(task.task_id), "approval_required")

    def test_secret_shaped_request_is_redacted(self) -> None:
        with TemporaryDirectory() as folder:
            task = ExternalCodingControlPlane(Path(folder), build_tool_environment_registry()).plan("token=do-not-show")
            self.assertNotIn("do-not-show", task.request_summary)

    def test_git_metadata_is_bounded_read_only(self) -> None:
        runtime = ExternalCodingControlPlane(Path.cwd(), build_tool_environment_registry())
        self.assertLess(len(runtime.repo_metadata("status")), 3001)
        self.assertEqual(runtime.repo_metadata("push"), "unsupported_git_metadata_operation")


class AutomationTests(unittest.TestCase):
    def test_status_is_read_only(self) -> None:
        runtime = LocalAutomationControlPlane(Path.cwd())
        self.assertTrue(runtime.preview(LocalAction.READ_SYSTEM_STATUS).allowed)
        self.assertFalse(runtime.status()["commands"])
        self.assertFalse(runtime.status()["filesystem_write"])

    def test_destructive_actions_blocked(self) -> None:
        runtime = LocalAutomationControlPlane(Path.cwd())
        for action in (LocalAction.DELETE_FILE, LocalAction.RUN_COMMAND, LocalAction.INSTALL_SOFTWARE, LocalAction.POWER_ACTION):
            preview = runtime.preview(action, "sensitive-target")
            self.assertFalse(preview.allowed)
            self.assertTrue(preview.approval_required)


class ConnectorTests(unittest.TestCase):
    def test_states_are_not_compressed_into_ready(self) -> None:
        item = ConnectorRegistry().get("github")
        self.assertTrue(item.discovered)
        self.assertFalse(item.configured)
        self.assertFalse(item.authenticated)
        self.assertFalse(item.enabled)
        self.assertFalse(item.healthy)

    def test_connector_test_is_non_destructive(self) -> None:
        registry = ConnectorRegistry()
        self.assertEqual(registry.test("telegram"), "not_configured")
        self.assertEqual(registry.audit[-1]["operation"], "metadata_test")

    def test_capability_collisions_are_visible(self) -> None:
        collisions = ConnectorRegistry().collisions()
        self.assertTrue(any(item.startswith("text_message:") for item in collisions))


class ObservabilityTests(unittest.TestCase):
    def test_metrics_and_traces_are_bounded_payload_free(self) -> None:
        runtime = ObservabilityRuntime(max_metrics=2, max_traces=2)
        for index in range(5): runtime.record("provider", "latency", index, "ms")
        span = runtime.span("provider", "health", 2.0)
        self.assertEqual(len(runtime.metrics), 2)
        self.assertFalse(span.payload_included)
        self.assertFalse(runtime.snapshot()["telemetry_upload"])

    def test_invalid_sensitive_labels_fail_closed(self) -> None:
        runtime = ObservabilityRuntime()
        with self.assertRaises(ValueError): runtime.record("provider", "token=secret", 1)


class Phase6OperationalCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = CommandManager(); self.manager.initialize()

    def test_required_commands_do_not_fall_through(self) -> None:
        commands = (
            "voice stt", "voice tts", "vision health", "camera status", "camera start", "coding health", "coding tools",
            "coding tool inspect aider", "git status", "git verify", "github branch", "system status", "system processes",
            "app list", "app open notepad", "file status", "file delete secret.txt", "automation status", "scheduler list",
            "connector status", "connector list", "connector capabilities", "connector inspect github", "connector test github",
            "performance status", "performance providers", "operations status", "operations audit",
            "voice test-input", "voice test-output", "voice sessions", "voice session inspect missing",
            "runtime traces", "runtime circuits", "phase6 status", "phase6 checklist",
        )
        for command in commands:
            with self.subTest(command=command):
                output = self.manager.execute(command).response
                self.assertNotIn("Unknown command", output)
                self.assertLess(len(output), 7000)
                self.assertNotIn("C:\\Users\\", output)

    def test_unknown_subcommands_return_bounded_help(self) -> None:
        for command in ("camera spy", "system shutdown-now", "connector authorize-all", "performance upload"):
            output = self.manager.execute(command).response
            self.assertIn("Unknown", output)
            self.assertLess(len(output), 2000)

    def test_candidate_report_preserves_authority_and_truthful_degradations(self) -> None:
        with TemporaryDirectory() as folder:
            runtime = Phase6Runtime(Path(folder))
            report = runtime.candidate_report()
            self.assertTrue(report.candidate_ready)
            self.assertFalse(runtime.execution_authority)
            self.assertIn("Deployment", report.degradations)
            self.assertFalse(runtime.status()["observability"]["telemetry_upload"])

    def test_project_status_reports_phase6_live_state(self) -> None:
        response = self.manager.execute("project status")
        self.assertIn("p6:cand:R", response.response)
        self.assertTrue(response.metadata["phase6_started"])
        self.assertFalse(response.metadata["phase6_execution_authority"])


if __name__ == "__main__":
    unittest.main()
