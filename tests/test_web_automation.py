"""Tests for governed read-only Web Automation."""

from __future__ import annotations

import json
import socket
import ssl
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import URLError

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
    ReadOnlyWebInspectionAdapter,
    UnavailableBrowserAdapter,
    _ValidatedRedirectHandler,
    _WebInspectionError,
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


def settings(enabled=False, mode="off", retention=100, allow_local=False, allow_http=False, max_bytes=524288, redirects=5):
    config = SimpleNamespace(
        enabled=enabled, mode=mode, adapter="read-only-http",
        allow_local_targets=allow_local, allow_http=allow_http,
        audit_retention=retention, action_timeout_seconds=2,
        maximum_redirects=redirects, maximum_response_bytes=max_bytes,
        maximum_preview_characters=2000,
    )
    return SimpleNamespace(web_automation=config)


class InspectionHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/error":
            self.send_error(503); return
        if self.path == "/redirect":
            self.send_response(302); self.send_header("Location", "/page"); self.end_headers(); return
        if self.path.startswith("/loop"):
            self.send_response(302); self.send_header("Location", "/loop"); self.end_headers(); return
        if self.path == "/binary":
            body = b"\x00\x01binary"; content_type = "application/octet-stream"
        elif self.path == "/large":
            body = b"x" * 4096; content_type = "text/plain"
        elif self.path == "/plain":
            body = b"Plain public text"; content_type = "text/plain"
        else:
            body = b"<html><head><title>Example Safe Page</title><meta name='description' content='A safe description'></head><body>Hello public page<script>hidden()</script> contact@example.com C:\\private\\file.txt AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA</body></html>"
            content_type = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers(); self.wfile.write(body)

    def log_message(self, format, *args):
        return


class LocalInspectionServer:
    def __enter__(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), InspectionHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"
        return self

    def __exit__(self, *_):
        self.server.shutdown(); self.server.server_close(); self.thread.join(timeout=2)


class WebAutomationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def manager(self, enabled=False, mode="off", adapter=None, retention=100, allow_local=False, allow_http=False, max_bytes=524288, redirects=5):
        return WebAutomationManager(self.root, settings(enabled, mode, retention, allow_local, allow_http, max_bytes, redirects), adapter)

    def test_initializes_disabled_with_truthful_unavailable_adapter(self):
        manager = WebAutomationManager(self.root, SimpleNamespace(web_automation=SimpleNamespace(enabled=False, mode="off", adapter="unavailable-browser", allow_local_targets=False, allow_http=False, audit_retention=100, action_timeout_seconds=8, maximum_redirects=5, maximum_response_bytes=524288, maximum_preview_characters=2000)))
        status = manager.status()
        self.assertTrue(status["initialized"])
        self.assertFalse(status["enabled"])
        self.assertFalse(status["adapter_available"])
        self.assertEqual(status["sensitive_actions"], "blocked")

    def test_manager_selects_real_adapter_without_heavy_dependency(self):
        manager = self.manager(True, "read_only")
        self.assertIsInstance(manager.adapter, ReadOnlyWebInspectionAdapter)
        self.assertTrue(manager.status()["network_inspection_enabled"])
        self.assertEqual(manager.adapter.adapter_id, "read-only-http")

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

    def test_link_local_metadata_and_sensitive_queries_are_blocked(self):
        manager = self.manager()
        for url in ("https://169.254.169.254/latest/meta-data", "https://[::1]/", "https://example.com/?access_token=secret", "https://example.com/?session=secret"):
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
        result = self.manager(True, "read_only", UnavailableBrowserAdapter()).open_url("https://example.com")
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

    def test_real_read_only_fetch_extracts_bounded_sanitized_snapshot(self):
        with LocalInspectionServer() as server:
            manager = self.manager(True, "read_only", allow_local=True, allow_http=True)
            result = manager.open_url(server.base_url + "/page")
            self.assertEqual(result.status, WebAutomationStatus.COMPLETED)
            snapshot = result.snapshot
            self.assertEqual(snapshot.title, "Example Safe Page")
            self.assertEqual(snapshot.description, "A safe description")
            self.assertIn("Hello public page", snapshot.text_preview)
            self.assertNotIn("hidden()", snapshot.text_preview)
            self.assertIn("[redacted-email]", snapshot.text_preview)
            self.assertIn("[redacted-path]", snapshot.text_preview)
            self.assertIn("[redacted-value]", snapshot.text_preview)
            self.assertFalse(snapshot.content_stored)
            self.assertFalse(snapshot.screenshot_stored)
            self.assertFalse((self.root / "page.html").exists())

    def test_safe_redirect_is_followed_and_recorded(self):
        with LocalInspectionServer() as server:
            manager = self.manager(True, "read_only", allow_local=True, allow_http=True)
            result = manager.open_url(server.base_url + "/redirect")
            self.assertEqual(result.status, WebAutomationStatus.COMPLETED)
            self.assertEqual(result.snapshot.redirect_count, 1)
            self.assertEqual(result.snapshot.redirect_domains, ("127.0.0.1",))
            self.assertEqual(manager.audit_events()[-1].redirect_count, 1)

    def test_redirect_loop_and_response_limits_fail_safely(self):
        with LocalInspectionServer() as server:
            loop_manager = self.manager(True, "read_only", allow_local=True, allow_http=True, redirects=1)
            self.assertEqual(loop_manager.open_url(server.base_url + "/loop").error_code, "WEB_TOO_MANY_REDIRECTS")
            size_manager = self.manager(True, "read_only", allow_local=True, allow_http=True, max_bytes=1024)
            self.assertEqual(size_manager.open_url(server.base_url + "/large").error_code, "WEB_RESPONSE_TOO_LARGE")
            self.assertEqual(size_manager.open_url(server.base_url + "/binary").error_code, "WEB_UNSUPPORTED_CONTENT_TYPE")

    def test_redirect_policy_rejects_unsafe_targets(self):
        manager = self.manager()
        handler = _ValidatedRedirectHandler(manager._validate_fetch_url, 5)
        for target in ("file:///private.txt", "http://127.0.0.1", "https://user:pass@example.com"):
            with self.subTest(target=target), self.assertRaises(_WebInspectionError) as caught:
                handler.redirect_request(None, None, 302, "Found", {}, target)
            self.assertEqual(caught.exception.code, "WEB_REDIRECT_BLOCKED")

    def test_dns_resolution_to_private_address_is_blocked(self):
        manager = self.manager(True, "read_only")
        fake = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]
        with patch("jarvis.web_automation.socket.getaddrinfo", return_value=fake):
            decision = manager._validate_fetch_url("https://public.example/")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "WEB_PRIVATE_NETWORK_BLOCKED")

    def test_http_timeout_dns_and_tls_failures_are_classified(self):
        with LocalInspectionServer() as server:
            manager = self.manager(True, "read_only", allow_local=True, allow_http=True)
            self.assertEqual(manager.open_url(server.base_url + "/error").error_code, "WEB_HTTP_ERROR")

        manager = self.manager(True, "read_only")
        fake_opener = SimpleNamespace()
        for reason, expected in (
            (socket.timeout(), "WEB_TIMEOUT"),
            (socket.gaierror(), "WEB_DNS_ERROR"),
            (ssl.SSLError("test"), "WEB_TLS_ERROR"),
        ):
            fake_opener.open = lambda *args, _reason=reason, **kwargs: (_ for _ in ()).throw(URLError(_reason))
            public_dns = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
            with self.subTest(expected=expected), patch("jarvis.web_automation.socket.getaddrinfo", return_value=public_dns), patch("jarvis.web_automation.build_opener", return_value=fake_opener):
                self.assertEqual(manager.open_url("https://example.com/").error_code, expected)

    def test_close_clears_only_in_memory_page_and_keeps_audit(self):
        with LocalInspectionServer() as server:
            manager = self.manager(True, "read_only", allow_local=True, allow_http=True)
            manager.open_url(server.base_url + "/page")
            count = len(manager.audit_events())
            self.assertEqual(manager.close().status, WebAutomationStatus.CLOSED)
            self.assertFalse(manager.sessions)
            self.assertFalse(manager.adapter.pages)
            self.assertGreater(len(manager.audit_events()), count)


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

    def test_real_read_only_command_flow(self):
        with LocalInspectionServer() as server:
            real = WebAutomationManager(Path(self.temp.name), settings(True, "read_only", allow_local=True, allow_http=True))
            context = ConversationContext(ConversationSession(), web_automation=real)
            opened = self.commands.execute(f"web open {server.base_url}/page", context)
            self.assertIn("completed", opened.response)
            self.assertIn("Example Safe Page", self.commands.execute("web title", context).response)
            self.assertIn("127.0.0.1", self.commands.execute("web url", context).response)
            snapshot = self.commands.execute("web snapshot", context).response
            self.assertIn("content_type=text/html", snapshot)
            self.assertIn("preview=", snapshot)
            self.assertIn("Web audit", self.commands.execute("web audit", context).response)
            self.assertIn("closed", self.commands.execute("web close", context).response)


if __name__ == "__main__":
    unittest.main()
