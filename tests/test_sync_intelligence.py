"""Behavioral tests for the governed online-sync foundation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from commands import CommandManager
from commands.command_help import CommandHelp
from conversation import ConversationContext, ConversationSession
from jarvis.sync_intelligence import (
    SyncConflictStrategy,
    SyncIntelligence,
    SyncItemType,
    SyncMode,
    SyncProviderInfo,
    SyncResult,
    SyncStatus,
)


class SuccessfulAdapter:
    provider_info = SyncProviderInfo("test-remote", True, True, True, "ready")

    def upload(self, item, timeout_seconds=15):
        return SyncResult(SyncStatus.SYNCED, "uploaded", item.sync_item_id)


class FailingAdapter:
    provider_info = SyncProviderInfo("test-failing", True, True, True, "ready")

    def upload(self, item, timeout_seconds=15):
        return SyncResult(SyncStatus.FAILED, "temporary failure", item.sync_item_id, "timeout", True)


class TimeoutAdapter:
    provider_info = SyncProviderInfo("test-timeout", True, True, True, "ready")

    def upload(self, item, timeout_seconds=15):
        raise TimeoutError("private diagnostic")


class SyncIntelligenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.sync = SyncIntelligence(self.root)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def payload(self, **extra):
        return {"id": "task-1", "title": "Safe task", "status": "active", "progress": 25, "updated_at": "2026-08-01", **extra}

    def test_manager_initializes_disabled_with_local_adapter(self):
        status = self.sync.status()
        self.assertTrue(self.sync.initialized)
        self.assertEqual(status["mode"], "off")
        self.assertFalse(status["enabled"])
        self.assertIn("local-queue", self.sync.adapters)
        self.assertFalse(status["remote_available"])

    def test_yaml_boolean_style_mode_fails_closed(self):
        settings = SimpleNamespace(sync=SimpleNamespace(mode=False, conflict_strategy="manual", adapter="local-queue", maximum_item_size=8192, maximum_queue_items=100, maximum_batch_size=10, maximum_attempts=3, completed_retention_count=25, audit_retention_count=100, maximum_nested_depth=4, maximum_string_length=1000))
        manager = SyncIntelligence(self.root / "boolean-mode", settings)
        self.assertEqual(manager.mode, SyncMode.OFF)

    def test_adapter_registration(self):
        adapter = SuccessfulAdapter(); self.sync.register_adapter(adapter)
        self.assertIs(self.sync.adapters["test-remote"], adapter)

    def test_enable_is_manual_only_and_disable_preserves_queue(self):
        self.sync.enqueue("task_summary", self.payload())
        self.assertEqual(self.sync.enable_manual().status, SyncStatus.READY)
        self.assertEqual(self.sync.mode, SyncMode.MANUAL)
        self.assertEqual(self.sync.disable().status, SyncStatus.DISABLED)
        self.assertEqual(self.sync.summary()["queued"], 1)

    def test_enqueue_approved_record_and_atomic_persistence(self):
        result = self.sync.enqueue(SyncItemType.TASK_SUMMARY, self.payload())
        self.assertEqual(result.status, SyncStatus.QUEUED)
        self.assertTrue(self.sync.queue_path.is_file())
        self.assertFalse(self.sync.queue_path.with_suffix(".json.tmp").exists())
        stored = json.loads(self.sync.queue_path.read_text(encoding="utf-8"))
        self.assertEqual(stored["items"][0]["sanitized_payload"]["title"], "Safe task")

    def test_list_inspect_cancel_and_retry(self):
        queued = self.sync.enqueue("task_summary", self.payload())
        self.assertEqual(len(self.sync.list_items()), 1)
        self.assertEqual(self.sync.inspect(queued.sync_item_id).item_type, "task_summary")
        self.assertEqual(self.sync.cancel(queued.sync_item_id).status, SyncStatus.CANCELLED)
        self.assertEqual(self.sync.retry(queued.sync_item_id).status, SyncStatus.INVALID)

    def test_unknown_type_and_unknown_field_rejected(self):
        self.assertEqual(self.sync.enqueue("raw_audio", {}).error_code, "unsupported_item_type")
        self.assertEqual(self.sync.enqueue("task_summary", self.payload(raw="x")).error_code, "unknown_fields")

    def test_secret_keys_and_values_rejected(self):
        for payload in (
            {"key": "api_key", "value": "safe", "updated_at": "now", "password": "x"},
            {"key": "preference", "value": "Bearer abcdefghijklmnop", "updated_at": "now"},
            {"key": "preference", "value": "sk-abcdefghijklmnop", "updated_at": "now"},
        ):
            with self.subTest(payload=payload):
                self.assertEqual(self.sync.enqueue("preference_summary", payload).status, SyncStatus.BLOCKED_BY_POLICY)

    def test_paths_binary_base64_oversize_and_deep_nesting_rejected(self):
        cases = (
            {"summary": "C:\\Users\\person\\private.txt", "topics": [], "updated_at": "now"},
            {"summary": b"binary", "topics": [], "updated_at": "now"},
            {"summary": "A" * 300 + "==", "topics": [], "updated_at": "now"},
            {"summary": "safe", "topics": [[[[["too deep"]]]]], "updated_at": "now"},
            {"summary": "x" * 1001, "topics": [], "updated_at": "now"},
        )
        for payload in cases:
            with self.subTest(payload_type=type(payload["summary"]).__name__):
                self.assertEqual(self.sync.enqueue("memory_summary", payload).status, SyncStatus.BLOCKED_BY_POLICY)

    def test_duplicate_prevention_and_capacity(self):
        first = self.sync.enqueue("task_summary", self.payload())
        duplicate = self.sync.enqueue("task_summary", self.payload())
        self.assertEqual(duplicate.sync_item_id, first.sync_item_id)
        self.assertEqual(duplicate.error_code, "duplicate_item")
        limited = SyncIntelligence(self.root / "limited", SimpleNamespace(sync=SimpleNamespace(mode="off", conflict_strategy="manual", adapter="local-queue", maximum_item_size=8192, maximum_queue_items=1, maximum_batch_size=1, maximum_attempts=1, completed_retention_count=1, audit_retention_count=5, maximum_nested_depth=4, maximum_string_length=1000)))
        limited.enqueue("task_summary", self.payload())
        self.assertEqual(limited.enqueue("goal_summary", {"id":"g","title":"Goal","status":"active","progress":0,"updated_at":"now"}).error_code, "queue_full")

    def test_malformed_storage_is_quarantined(self):
        self.sync.queue_path.write_text("not-json", encoding="utf-8")
        recovered = SyncIntelligence(self.root)
        self.assertEqual(recovered.summary()["total"], 0)
        self.assertTrue(tuple(self.root.glob("queue.corrupt-*.json")))

    def test_unavailable_remote_never_marks_synced(self):
        item = self.sync.enqueue("task_summary", self.payload())
        self.sync.enable_manual()
        result = self.sync.run()
        self.assertEqual(result.status, SyncStatus.UNAVAILABLE)
        self.assertEqual(self.sync.inspect(item.sync_item_id).status, "queued")

    def test_success_and_bounded_retry(self):
        item = self.sync.enqueue("task_summary", self.payload())
        self.sync.enable_manual(); self.sync.register_adapter(SuccessfulAdapter()); self.sync.selected_adapter = "test-remote"
        result = self.sync.run()
        self.assertEqual((result.synced, self.sync.inspect(item.sync_item_id).status), (1, "synced"))
        failing = SyncIntelligence(self.root / "failure"); failed_item = failing.enqueue("task_summary", self.payload())
        failing.enable_manual(); failing.register_adapter(FailingAdapter()); failing.selected_adapter = "test-failing"
        failure = failing.run(); stored = failing.inspect(failed_item.sync_item_id)
        self.assertEqual(failure.failed, 1); self.assertEqual(stored.attempt_count, 1); self.assertIsNotNone(stored.next_retry_at)

    def test_timeout_is_normalized_without_private_diagnostic(self):
        item = self.sync.enqueue("task_summary", self.payload())
        self.sync.enable_manual(); self.sync.register_adapter(TimeoutAdapter()); self.sync.selected_adapter = "test-timeout"
        result = self.sync.run()
        self.assertEqual(result.results[0].error_code, "timeout")
        self.assertNotIn("private diagnostic", result.results[0].message)
        self.assertEqual(self.sync.inspect(item.sync_item_id).status, "failed")

    def test_nested_project_health_fields_are_allowlisted(self):
        payload = {"release":"v","commit":"c","overall_mvp_readiness":64,"updated_at":"now","categories":[{"name":"Core","status":"Working","confidence":90,"evidence":"tests","next_action":"maintain","raw_log":"blocked"}]}
        self.assertEqual(self.sync.enqueue("project_health", payload).error_code, "unknown_fields")

    def test_conflict_detection_defaults_manual_and_no_overwrite(self):
        item = self.sync.enqueue("task_summary", self.payload())
        conflict = self.sync.detect_conflict(item.sync_item_id, "different", 2)
        self.assertEqual(conflict.strategy, SyncConflictStrategy.MANUAL.value)
        self.assertEqual(self.sync.inspect(item.sync_item_id).status, "conflict")
        self.assertEqual(self.sync.inspect(item.sync_item_id).sanitized_payload["title"], "Safe task")

    def test_cleanup_and_audit_are_bounded(self):
        item = self.sync.enqueue("task_summary", self.payload())
        self.sync.cancel(item.sync_item_id)
        self.sync.limits = type(self.sync.limits)(completed_retention_count=0, audit_retention_count=2)
        result = self.sync.cleanup()
        self.assertEqual(result["remaining"], 0)
        self.assertLessEqual(len(self.sync.audit_events()), 2)

    def test_installation_identity_is_random_local_uuid_and_not_normal_status(self):
        self.assertEqual(self.sync.installation_id, json.loads(self.sync.installation_path.read_text())["installation_id"])
        self.assertNotIn(self.sync.installation_id, json.dumps(self.sync.status()))

    def test_queue_file_contains_no_forbidden_raw_data(self):
        self.sync.enqueue("project_status", {"release":"v0.4.0-alpha","commit":"abc","primary_mode":"CLI","overall_mvp_readiness":62,"working_categories":6,"partial_categories":8,"experimental_categories":1,"next_milestone":"Prompt 33","updated_at":"2026-08-01"})
        text = self.sync.queue_path.read_text(encoding="utf-8").lower()
        for forbidden in ("api_key", ".env", "conversation history", ".wav", ".png", "authorization"):
            self.assertNotIn(forbidden, text)

    def test_runtime_sync_files_are_ignored_by_git_policy(self):
        ignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("data/*", ignore)


class SyncCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.sync = SyncIntelligence(Path(self.temp.name))
        self.commands = CommandManager(); self.commands.initialize()
        self.context = ConversationContext(ConversationSession(), sync_intelligence=self.sync)

    def tearDown(self): self.temp.cleanup()

    def execute(self, text): return self.commands.execute(text, self.context)

    def test_status_on_off_and_help(self):
        self.assertIn("mode=off", self.execute("sync status").response)
        self.assertIn("manual/local queue", self.execute("sync on").response)
        self.assertIn("mode=manual", self.execute("sync status").response)
        self.assertIn("preserved", self.execute("sync off").response)
        self.assertIn("sync status", CommandHelp().render(self.commands.registry))

    def test_add_queue_summary_inspect_cancel_cleanup(self):
        add = self.execute("sync add project_status")
        item_id = add.metadata["sync_item_id"]
        self.assertIn("queued", add.response)
        self.assertIn(item_id, self.execute("sync queue").response)
        self.assertIn("queued=1", self.execute("sync queue summary").response)
        self.assertIn("project_status", self.execute(f"sync inspect {item_id}").response)
        self.assertIn("cancelled", self.execute(f"sync cancel {item_id}").response)
        self.assertIn("removed=", self.execute("sync cleanup").response)

    def test_run_conflicts_retry_and_invalid_input(self):
        self.execute("sync on"); self.execute("sync add project_status")
        self.assertIn("unavailable", self.execute("sync run").response)
        self.assertIn("none", self.execute("sync conflicts").response)
        self.assertIn("not found", self.execute("sync retry missing").response.lower())
        self.assertIn("valid JSON", self.execute("sync add task_summary not-json").response)
        self.assertIn("Usage", self.execute("sync inspect").response)

    def test_commands_do_not_require_provider_or_network(self):
        response = self.execute("sync status")
        self.assertTrue(response.metadata["deployment_status_only"])
        self.assertFalse(response.metadata["remote_available"])


if __name__ == "__main__":
    unittest.main()
