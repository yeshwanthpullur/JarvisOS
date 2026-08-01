"""Tests for governed read-only Web Automation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from commands import CommandManager
from conversation import ConversationContext, ConversationSession
from jarvis.web_automation import (
    WebActionRequest,
    WebActionResult,
    WebActionType,
    WebAutomationManager,
    WebAutomationStatus,
    WebPageSnapshot,
    WebPermission,
)


class FakeReadOnlyAdapter:
    adapter_id = "fake-read-only"
    available = True
    capabilities = (
        WebActionType.OPEN_URL,
        WebActionType.GET_PAGE_TITLE,
        WebActionType.GET_CURRENT_URL,
        WebActionType.SNAPSHOT_PAGE,
        WebActionType.CLOSE_SESSION,
    )

    def open_url(self, url, request_id):
        return WebActionResult(request_id, WebActionType.OPEN_URL, WebAutomationStatus.COMPLETED, "Read-only page opened.", "session-1", "example.com", current_url=url)

    def get_page_title(self, session_id, request_id):
        return WebActionResult(request_id, WebActionType.GET_PAGE_TITLE, WebAutomationStatus.COMPLETED, "Page title read.", session_id, "example.com", title="Example Domain")

    def get_current_url(self, session_id, request_id):
        return WebActionResult(request_id, WebActionType.GET_CURRENT_URL, WebAutomationStatus.COMPLETED, "Current URL read.", session_id, "example.com", current_url="https://example.com/?token=private-value")

    def snapshot_page(self, session_id, request_id):
        snapshot = WebPageSnapshot(session_id, "example.com", "Example Domain", "https://example.com/", "2026-08-02T00:00:00+00:00")
        return WebActionResult(request_id, WebActionType.SNAPSHOT_PAGE, WebAutomationStatus.COMPLETED, "Page metadata captured without content.", session_id, "example.com", snapshot=snapshot)

    def close_session(self, session_id, request_id):
        return WebActionResult(request_id, WebActionType.CLOSE_SESSION, WebAutomationStatus.COMPLETED, "Web session closed.", session_id, "example.com")


def settings(enabled=False, mode="off", retention=100, allow_local=False):
    config = SimpleNamespace(enabled=enabled, mode=mode, allow_local_targets=allow_local, audit_retention=retention)
    return SimpleNamespace(web_automation=config)


class WebAutomationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def manager(self, enabled=False, mode="off", adapter=None, retention=100, allow_local=False):
        return WebAutomationManager(self.root, settings(enabled, mode, retention, allow_local), adapter)

    def test_initializes_disabled_with_truthful_unavailable_adapter(self):
        manager = self.manager()
        status = manager.status()
        self.assertTrue(status["initialized"])
        self.assertFalse(status["enabled"])
        self.assertFalse(status["adapter_available"])
        self.assertEqual(status["sensitive_actions"], "blocked")

    def test_valid_https_url_is_normalized(self):
        decision = self.manager().policy(WebActionType.OPEN_URL, "HTTPS://Example.COM/path#fragment")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.safe_domain, "example.com")
        self.assertNotIn("fragment", decision.normalized_url)

    def test_unsafe_schemes_credentials_and_local_targets_are_blocked(self):
        manager = self.manager()
        for url in ("file:///private.txt", "javascript:alert(1)", "ftp://example.com/file", "https://user:pass@example.com", "http://127.0.0.1", "http://localhost", "http://10.1.2.3"):
            with self.subTest(url=url):
                self.assertFalse(manager.policy(WebActionType.OPEN_URL, url).allowed)

    def test_unsafe_topics_and_bypass_requests_are_blocked(self):
        manager = self.manager()
        for url in ("https://casino.example/", "https://example.com/captcha-bypass", "https://malware.example/"):
            with self.subTest(url=url):
                self.assertEqual(manager.open_url(url).status, WebAutomationStatus.BLOCKED_BY_POLICY)

    def test_sensitive_actions_are_blocked_before_adapter(self):
        manager = self.manager(True, "read_only", FakeReadOnlyAdapter())
        for action in (WebActionType.CLICK, WebActionType.TYPE_TEXT, WebActionType.SUBMIT_FORM, WebActionType.DOWNLOAD, WebActionType.UPLOAD, WebActionType.LOGIN, WebActionType.PURCHASE, WebActionType.SEND_MESSAGE, WebActionType.DELETE, WebActionType.ACCOUNT_CHANGE):
            result = manager.execute(WebActionRequest("r", action, permissions=(WebPermission.CLICK,)))
            self.assertEqual(result.status, WebAutomationStatus.BLOCKED_BY_POLICY)
            self.assertTrue(result.approval_required)

    def test_disabled_manager_does_not_fake_open(self):
        result = self.manager(adapter=FakeReadOnlyAdapter()).open_url("https://example.com")
        self.assertEqual(result.status, WebAutomationStatus.DISABLED)

    def test_unavailable_adapter_does_not_fake_open(self):
        result = self.manager(True, "read_only").open_url("https://example.com")
        self.assertEqual(result.status, WebAutomationStatus.UNAVAILABLE)

    def test_real_adapter_contract_supports_only_read_only_metadata(self):
        manager = self.manager(True, "read_only", FakeReadOnlyAdapter())
        opened = manager.open_url("https://example.com")
        self.assertEqual(opened.status, WebAutomationStatus.COMPLETED)
        self.assertEqual(manager.title().title, "Example Domain")
        self.assertIn("redacted=1", manager.safe_url_for_display(manager.current_url().current_url))
        snapshot = manager.snapshot().snapshot
        self.assertIsNotNone(snapshot)
        self.assertFalse(snapshot.content_stored)
        self.assertFalse(snapshot.screenshot_stored)
        self.assertEqual(manager.close().status, WebAutomationStatus.COMPLETED)
        self.assertFalse(manager.sessions)

    def test_missing_permission_is_rejected_when_scope_is_explicit(self):
        decision = self.manager().policy(WebActionType.SNAPSHOT_PAGE, permissions=(WebPermission.PAGE_READ,))
        self.assertFalse(decision.allowed)

    def test_audit_is_redacted_atomic_and_bounded(self):
        manager = self.manager(True, "read_only", FakeReadOnlyAdapter(), retention=2)
        manager.open_url("https://example.com/?token=do-not-store")
        manager.title("session-1")
        manager.current_url("session-1")
        self.assertEqual(len(manager.audit_events()), 2)
        text = manager.audit_path.read_text(encoding="utf-8")
        self.assertNotIn("do-not-store", text)
        self.assertNotIn("token=", text)
        self.assertNotIn("Example Domain", text)
        self.assertEqual(len(json.loads(text)["events"]), 2)

    def test_audit_recovery_from_malformed_file_is_safe(self):
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "audit.json").write_text("not-json", encoding="utf-8")
        self.assertEqual(self.manager().audit_events(), ())

    def test_runtime_storage_is_ignored(self):
        ignore = (Path(__file__).resolve().parents[1] / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("data/*", ignore)


class WebCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.web = WebAutomationManager(Path(self.temp.name), settings())
        self.commands = CommandManager(); self.commands.initialize()
        self.context = ConversationContext(ConversationSession(), web_automation=self.web)

    def tearDown(self): self.temp.cleanup()
    def execute(self, text): return self.commands.execute(text, self.context)

    def test_status_policy_and_session_commands(self):
        self.assertIn("mode=off", self.execute("web status").response)
        self.assertIn("sensitive_actions=blocked", self.execute("web status").response)
        self.assertIn("Click, type, submit", self.execute("web policy").response)
        self.assertIn("none", self.execute("web session").response)

    def test_open_and_read_commands_fail_truthfully_without_adapter(self):
        self.assertIn("disabled", self.execute("web open https://example.com").response)
        for command in ("web title", "web url", "web snapshot", "web close"):
            self.assertIn("disabled", self.execute(command).response)
        self.assertIn("Web audit", self.execute("web audit").response)

    def test_bad_and_unsafe_urls_are_blocked_without_crash(self):
        self.assertIn("Usage", self.execute("web open").response)
        self.assertIn("blocked_by_policy", self.execute("web open file:///secret.txt").response)
        self.assertIn("blocked_by_policy", self.execute("web open https://user:pass@example.com").response)


if __name__ == "__main__":
    unittest.main()
