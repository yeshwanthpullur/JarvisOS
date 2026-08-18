"""Prompt 99 cross-subsystem integration and release-candidate checks."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from commands import CommandManager
from config import load_settings
from conversation.conversation_routing import ConversationIntent, classify_conversation_route
from jarvis.phase6.automation import LocalAction
from jarvis.phase6.integration import CheckState
from jarvis.phase6.memory import MemoryType
from jarvis.phase6.runtime import Phase6Runtime
from jarvis.phase6.web import BrowserSession, WebAction


ROOT = Path(__file__).resolve().parents[1]


class RoutingIntegrationTests(unittest.TestCase):
    def test_normal_chat_commands_and_explicit_goal_routing_remain_distinct(self) -> None:
        chat = (
            "Who are you?", "Tell me a joke.", "Explain recursion.",
            "Write one sentence about Python.", "What is the capital of France?",
        )
        for prompt in chat:
            with self.subTest(prompt=prompt):
                self.assertIn(classify_conversation_route(prompt).intent, {ConversationIntent.CASUAL, ConversationIntent.EXPLANATION, ConversationIntent.WRITING, ConversationIntent.FACTUAL_QA, ConversationIntent.GENERAL_CHAT})
        self.assertEqual(classify_conversation_route("Create a goal to improve JarvisOS.").intent, ConversationIntent.GOAL_CREATE)
        for command in ("goal status", "provider status", "conversation status"):
            self.assertEqual(classify_conversation_route(command, command_matched=True).intent, ConversationIntent.COMMAND)

    def test_phase6_commands_are_bounded_and_do_not_fall_through(self) -> None:
        manager = CommandManager(); manager.initialize()
        commands = (
            "phase6 status", "phase6 checklist", "environment status", "provider inspect ollama",
            "browser permissions", "research health", "document health", "memory health",
            "voice stt", "vision health", "coding health", "automation permissions",
            "connector status", "mcp status", "plugin status", "runtime health", "operations status",
        )
        for command in commands:
            with self.subTest(command=command):
                response = manager.execute(command).response
                self.assertNotIn("Unknown command", response)
                self.assertLess(len(response), 7000)
                self.assertNotIn(str(ROOT), response)

    def test_phase6_flags_reach_bounded_diagnostics(self) -> None:
        manager = CommandManager(); manager.initialize()
        audit = manager.execute("environment audit --pip-check").response
        self.assertNotIn("pip_check=not_run", audit)
        candidate = manager.execute("phase6 candidate --probe").response
        self.assertIn("candidate_ready=True", candidate)


class AuthorityIntegrationTests(unittest.TestCase):
    def test_phase6_never_becomes_execution_authority(self) -> None:
        runtime = Phase6Runtime(ROOT)
        self.assertFalse(runtime.execution_authority)
        self.assertFalse(runtime.web.status()["execution_authority"])
        self.assertFalse(runtime.documents.status()["automatic_memory_update"])
        self.assertFalse(runtime.memory.status()["automatic_write"])
        self.assertEqual(runtime.automation.status()["authority"], "execution_policy_approval_broker")
        self.assertEqual(runtime.observability.snapshot()["authority"], "informational_only")

    def test_high_risk_web_coding_and_file_actions_fail_closed(self) -> None:
        runtime = Phase6Runtime(ROOT)
        self.assertFalse(runtime.web.decide(WebAction.SUBMIT_FORM, approved=True).allowed)
        task = runtime.coding.plan("fix this automatically")
        self.assertEqual(runtime.coding.apply(task.task_id), "approval_required")
        self.assertFalse(runtime.automation.preview(LocalAction.DELETE_FILE, ".env").allowed)

    def test_memory_namespace_and_authority_are_enforced(self) -> None:
        runtime = Phase6Runtime(ROOT)
        with self.assertRaises(PermissionError):
            runtime.memory.propose("session-a", "safe fact", MemoryType.SESSION_MEMORY, "test")
        item = runtime.memory.propose("session-a", "safe fact", MemoryType.SESSION_MEMORY, "test", authoritative=True)
        self.assertEqual(len(runtime.memory.search("safe", "session-b")), 0)
        self.assertEqual(runtime.memory.search("safe", "session-a")[0].memory_id, item.memory_id)
        with self.assertRaises(ValueError):
            runtime.memory.propose("session-a", "token=private-value", MemoryType.SESSION_MEMORY, "test", authoritative=True)


class FailureAndLifecycleTests(unittest.TestCase):
    def test_optional_components_missing_do_not_break_startup(self) -> None:
        with TemporaryDirectory() as folder:
            runtime = Phase6Runtime(Path(folder))
            status = runtime.status()
            self.assertEqual(status["phase"], 6)
            self.assertFalse(status["execution_authority"])
            self.assertTrue(status["documents"]["builtin_text"])
            self.assertFalse(status["connectors"]["auto_enable"])

    def test_invalid_inputs_and_missing_adapters_are_bounded(self) -> None:
        with TemporaryDirectory() as folder:
            runtime = Phase6Runtime(Path(folder))
            self.assertEqual(runtime.documents.parse("missing.pdf").status, "blocked")
            self.assertEqual(runtime.web.run_crawl("http://127.0.0.1/private").status, "blocked")
            self.assertEqual(runtime.connectors.test("missing"), "connector_not_found")
            self.assertIn(runtime.voice.stt().status, {"unavailable", "detected_disabled"})

    def test_explicit_sessions_close_and_bounded_state_survives_stress(self) -> None:
        runtime = Phase6Runtime(ROOT)
        for index in range(100):
            runtime.observability.record("conversation", "turn", index)
            runtime.web.plan_crawl(f"https://example.com/topic-{index}")
        runtime.web.sessions["session-test"] = BrowserSession("session-test", "metadata", "test", ("example.com",))
        self.assertTrue(runtime.web.close("session-test"))
        self.assertEqual(runtime.web.sessions["session-test"].status, "closed")
        self.assertLessEqual(len(runtime.observability.metrics), 500)
        self.assertLessEqual(len(runtime.web.audit), 100)


class CandidateAndTrackingTests(unittest.TestCase):
    def test_candidate_checklist_is_truthful(self) -> None:
        report = Phase6Runtime(ROOT).candidate_report()
        self.assertTrue(report.candidate_ready)
        self.assertFalse(report.critical_blockers)
        self.assertTrue(any(item.state is CheckState.DEGRADED for item in report.checks))
        self.assertEqual(next(item for item in report.checks if item.component == "Deployment").state, CheckState.NOT_TESTED)

    def test_phase6_configuration_defaults_are_fail_closed(self) -> None:
        settings = load_settings()
        self.assertFalse(settings.phase6.allow_automatic_install)
        self.assertFalse(settings.phase6.allow_automatic_model_download)
        self.assertFalse(settings.automation.commands_enabled)
        self.assertFalse(settings.automation.filesystem_write_allowed)
        self.assertFalse(settings.models.allow_cloud_providers)
        self.assertFalse(settings.connectors.auto_enable)
        self.assertFalse(settings.connectors.auto_authenticate)
        self.assertFalse(settings.observability.telemetry_upload)
        self.assertFalse(settings.voice.continuous_listening)
        self.assertFalse(settings.vision.camera_enabled)

    def test_vercel_remains_bounded_status_only(self) -> None:
        source = (ROOT / "api" / "index.py").read_text(encoding="utf-8")
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        self.assertNotIn("Phase6Runtime", source)
        self.assertNotIn("main.py", json.dumps(config))
        self.assertNotIn("jarvis-os-6oy2", source)


if __name__ == "__main__":
    unittest.main()
