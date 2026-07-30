from __future__ import annotations

import json
import socket
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from commands import CommandManager
from config.schema import InterfaceConfig
from conversation.conversation_response import ConversationResponse
from conversation.conversation_session import ConversationSession
from server.local_interface import LocalInterfaceService, redact_text


class FakeHistory:
    def list(self):
        return ()


class FakeProviderExecution:
    initialized = True
    history = FakeHistory()


class FakeConversation:
    def __init__(self) -> None:
        self.initialized = True
        self.command_manager = CommandManager()
        self.command_manager.initialize()
        self.active_session = ConversationSession()
        self.records: list[tuple[str, str | None]] = []
        self._messages: dict[str, list[dict[str, object]]] = {self.active_session.conversation_id: []}

    def handle_input(self, message: str, request_id: str | None = None) -> ConversationResponse:
        self.records.append((message, request_id))
        is_command = self.command_manager.registry.lookup(self.command_manager.parser.parse(message.lower()).name) is not None
        response = "command-ok" if is_command else "provider-ok"
        self._messages[self.active_session.conversation_id].extend((
            {"role": "user", "content": message, "timestamp": "now"},
            {"role": "assistant", "content": response, "timestamp": "now", "status": "completed", "metadata": {}},
        ))
        return ConversationResponse(
            response=response,
            execution_summary={} if is_command else {"provider_id": "mock-local", "model_id": "mock-model", "strategy": "direct"},
            metadata={"jarvis_request_id": request_id},
        )

    def create_conversation(self) -> ConversationSession:
        self.active_session = ConversationSession()
        self._messages[self.active_session.conversation_id] = []
        return self.active_session

    def activate_conversation(self, conversation_id: str) -> bool:
        if conversation_id not in self._messages:
            return False
        self.active_session.conversation_id = conversation_id
        return True

    def list_conversations(self):
        return tuple({"conversation_id": key, "title": "Conversation", "turns": len(value) // 2, "updated_at": "now", "active": key == self.active_session.conversation_id} for key, value in self._messages.items())

    def conversation_messages(self, conversation_id: str, limit: int = 200):
        values = self._messages.get(conversation_id)
        return None if values is None else tuple(values[-limit:])


class FakeVoice:
    initialized = True
    enabled = False
    input_enabled = False
    output_enabled = True
    mode = SimpleNamespace(value="off")
    privacy_mode = "strict"
    selected_input_backend = "offline-stt"
    selected_output_backend = "windows-sapi"
    language = "en-US"
    rate = 0
    volume = 80
    raw_audio_persistence = False
    interrupted = False

    def health(self):
        return {"windows-sapi": {"status": "healthy"}, "offline-stt": {"status": "unavailable"}}

    def devices(self, direction=None):
        return () if direction == "input" else (SimpleNamespace(device_id="default-output"),)

    def say(self, text, parent_request_id):
        return SimpleNamespace(status=SimpleNamespace(value="completed"), synthesis_id="synth-1", backend_id="windows-sapi", audio_reference="local.wav")

    def interrupt(self):
        changed = not self.interrupted
        self.interrupted = True
        return changed


class FakeTools:
    mode = SimpleNamespace(value="automatic-safe")
    limits = SimpleNamespace(maximum_per_request=3)

    def list_tools(self):
        return (SimpleNamespace(tool_id="safe.calc", name="Calculator", description="Safe arithmetic", capabilities=("calculate",), risk_class=SimpleNamespace(value="minimal"), permissions=("tool.execute",), enabled=True, available=True, healthy=True),)

    def cancel(self, invocation_id):
        return invocation_id == "active-tool"


class FakePlanning:
    mode = SimpleNamespace(value="confirm")
    limits = SimpleNamespace(maximum_steps=12)
    plans = {}

    def cancel(self, plan_id):
        return self.plans[plan_id]


class FakeStore:
    def list(self):
        return ()

    def get(self, coordination_id):
        return None


class FakeOrchestrator:
    mode = SimpleNamespace(value="confirm")
    limits = SimpleNamespace(maximum_agents=4)
    store = FakeStore()

    def cancel(self, coordination_id):
        return coordination_id == "active-coordination"


class FakeStartup:
    def __init__(self, root: Path) -> None:
        log_dir = root / "logs"
        log_dir.mkdir()
        (log_dir / "jarvis.log").write_text(
            "2026-01-01 | INFO | provider | request completed api_key=topsecret\n"
            "2026-01-01 | ERROR | reasoning | hidden reasoning should stay private\n",
            encoding="utf-8",
        )
        self.settings = SimpleNamespace(
            logs_dir=log_dir,
            logging=SimpleNamespace(log_file="jarvis.log"),
            data_dir=root,
        )
        self.status = SimpleNamespace(state=SimpleNamespace(value="running"))
        self.health_results = ()
        self.conversation_manager = FakeConversation()
        self.provider_execution_manager = FakeProviderExecution()
        self.provider_manager = SimpleNamespace(registry=SimpleNamespace(all=lambda: ()))
        self.jarvis_core = SimpleNamespace(manager=SimpleNamespace(voice_intelligence=FakeVoice(), tools=FakeTools(), autonomous_planning=FakePlanning()))
        self.agent_manager = SimpleNamespace(orchestrator=FakeOrchestrator())


def free_port() -> int:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


class LocalInterfaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.port = free_port()
        self.config = replace(
            InterfaceConfig(),
            port=self.port,
            open_browser=False,
            event_timeout=1,
            allowed_origins=(f"http://127.0.0.1:{self.port}", f"http://localhost:{self.port}"),
        )
        self.startup = FakeStartup(self.root)
        self.service = LocalInterfaceService(self.startup, self.config)

    def tearDown(self) -> None:
        self.service.stop()
        self.temp.cleanup()

    def start(self) -> None:
        self.service.start(background=True, open_browser=False)

    def get(self, path: str, **headers: str):
        request = urllib.request.Request(self.service.url + path, headers=headers)
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, response.headers, response.read()

    def post(self, path: str, payload: dict[str, object], *, token: str | None = None, origin: str | None = None):
        headers = {"Content-Type": "application/json", "X-Jarvis-Session": token or self.service.session_token}
        if origin:
            headers["Origin"] = origin
        request = urllib.request.Request(self.service.url + path, data=json.dumps(payload).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, json.load(response)

    def test_interface_disabled_by_default(self):
        self.assertFalse(InterfaceConfig().enabled)

    def test_loopback_is_default(self):
        self.assertEqual(InterfaceConfig().host, "127.0.0.1")

    def test_remote_binding_blocked(self):
        with self.assertRaises(ValueError):
            LocalInterfaceService(self.startup, replace(self.config, host="0.0.0.0"))

    def test_remote_flag_remains_unsupported(self):
        with self.assertRaises(ValueError):
            LocalInterfaceService(self.startup, replace(self.config, allow_remote=True))

    def test_bootstrap_endpoint(self):
        self.start(); status, headers, body = self.get("/api/bootstrap")
        data = json.loads(body)
        self.assertEqual(status, 200); self.assertEqual(data["application"], "JARVIS OS"); self.assertEqual(headers["X-Frame-Options"], "DENY")

    def test_health_endpoint(self):
        self.start(); _, _, body = self.get("/api/health")
        self.assertEqual(json.loads(body)["interface"], "healthy")

    def test_index_injects_token_without_url(self):
        self.start(); _, _, body = self.get("/")
        text = body.decode(); self.assertIn(self.service.session_token, text); self.assertNotIn("__JARVIS_SESSION_TOKEN__", text); self.assertNotIn(self.service.session_token, self.service.url)

    def test_static_assets_are_responsive(self):
        self.start(); _, _, body = self.get("/app.css")
        css = body.decode(); self.assertIn("@media (max-width: 760px)", css); self.assertIn("prefers-reduced-motion", css)

    def test_missing_token_rejected(self):
        self.start()
        request = urllib.request.Request(self.service.url + "/api/conversations", data=b"{}", headers={"Content-Type": "application/json"}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as caught: urllib.request.urlopen(request, timeout=5)
        self.assertEqual(caught.exception.code, 403)

    def test_invalid_token_rejected(self):
        self.start()
        with self.assertRaises(urllib.error.HTTPError) as caught: self.post("/api/conversations", {}, token="wrong")
        self.assertEqual(caught.exception.code, 403)

    def test_invalid_origin_rejected(self):
        self.start()
        with self.assertRaises(urllib.error.HTTPError) as caught: self.post("/api/conversations", {}, origin="https://evil.example")
        self.assertEqual(caught.exception.code, 403)

    def test_valid_local_origin_allowed(self):
        self.start(); status, data = self.post("/api/conversations", {}, origin=self.service.url)
        self.assertEqual(status, 200); self.assertEqual(data["status"], "completed")

    def test_malformed_json_rejected(self):
        self.start()
        request = urllib.request.Request(self.service.url + "/api/messages", data=b"{", headers={"Content-Type": "application/json", "X-Jarvis-Session": self.service.session_token}, method="POST")
        with self.assertRaises(urllib.error.HTTPError) as caught: urllib.request.urlopen(request, timeout=5)
        self.assertEqual(caught.exception.code, 400)

    def test_oversized_request_rejected(self):
        config = replace(self.config, max_request_size=8)
        service = LocalInterfaceService(self.startup, config); service.start(background=True, open_browser=False)
        try:
            request = urllib.request.Request(service.url + "/api/messages", data=b'{"message":"long"}', headers={"Content-Type": "application/json", "X-Jarvis-Session": service.session_token}, method="POST")
            with self.assertRaises(urllib.error.HTTPError) as caught: urllib.request.urlopen(request, timeout=5)
            self.assertEqual(caught.exception.code, 413)
        finally: service.stop()

    def test_direct_message_preserves_request_id(self):
        result = self.service.submit_message({"message": "hello"})
        self.assertEqual(result.interface_request_id, result.jarvis_request_id); self.assertEqual(self.startup.conversation_manager.records[-1][1], result.interface_request_id)

    def test_ordinary_chat_normalizes_provider_metadata(self):
        result = self.service.submit_message({"message": "hello"})
        self.assertEqual(result.content, "provider-ok"); self.assertEqual(result.provider_id, "mock-local"); self.assertEqual(result.model_id, "mock-model")

    def test_command_stays_on_command_path(self):
        result = self.service.submit_message({"message": "voice status"})
        self.assertEqual(result.response_type, "command"); self.assertEqual(result.command_name, "voice status"); self.assertEqual(result.content, "command-ok")

    def test_async_message_returns_accepted_then_completed(self):
        self.start(); _, accepted = self.post("/api/messages", {"message": "hello"})
        self.assertEqual(accepted["status"], "accepted")
        deadline = time.time() + 3
        while time.time() < deadline:
            _, _, body = self.get(f"/api/requests/{accepted['interface_request_id']}")
            result = json.loads(body)
            if result["status"] != "accepted": break
            time.sleep(.02)
        self.assertEqual(result["status"], "completed"); self.assertEqual(result["content"], "provider-ok")

    def test_new_and_load_conversation(self):
        created = self.service.create_conversation({})
        loaded = self.service.conversation(created["conversation_id"])
        self.assertEqual(loaded["status"], "completed")

    def test_missing_conversation_is_truthful(self):
        self.assertEqual(self.service.conversation("missing")["status"], "unavailable")

    def test_cancel_active_request(self):
        event = threading.Event(); self.service._active_requests["request-1"] = event
        result = self.service.cancel({"request_id": "request-1"})
        self.assertTrue(result["cancelled"]); self.assertTrue(event.is_set())

    def test_cancel_missing_request_is_truthful(self):
        self.startup.jarvis_core.manager.voice_intelligence.interrupted = True
        result = self.service.cancel({"request_id": "missing"})
        self.assertFalse(result["cancelled"]); self.assertEqual(result["status"], "unavailable")

    def test_tool_listing_uses_authoritative_registry(self):
        tools = self.service.tools()
        self.assertEqual(tools[0]["tool_id"], "safe.calc"); self.assertEqual(tools[0]["risk_class"], "minimal")

    def test_missing_tool_is_truthful(self):
        self.assertEqual(self.service.tool("missing")["status"], "unavailable")

    def test_voice_status_is_honest(self):
        voice = self.service.voice_status()
        self.assertFalse(voice["microphone_available"]); self.assertEqual(voice["stt_status"], "unavailable"); self.assertEqual(voice["tts_status"], "healthy")

    def test_voice_synthesis_uses_voice_intelligence(self):
        result = self.service.speak({"text": "hello"})
        self.assertEqual(result["status"], "completed"); self.assertEqual(result["backend_id"], "windows-sapi")

    def test_voice_stop_uses_voice_intelligence(self):
        self.assertTrue(self.service.stop_voice({})["stopped"])

    def test_safe_logs_redact_secrets_and_reasoning(self):
        logs = self.service.safe_logs({})
        rendered = json.dumps(logs)
        self.assertNotIn("topsecret", rendered); self.assertNotIn("hidden reasoning", rendered.lower()); self.assertIn("REDACTED", rendered)

    def test_safe_logs_filter(self):
        logs = self.service.safe_logs({"level": ["ERROR"]})
        self.assertEqual(len(logs), 1); self.assertEqual(logs[0]["level"], "ERROR")

    def test_redaction_handles_bearer_tokens(self):
        redacted = redact_text("Authorization: Bearer abc.def")
        self.assertNotIn("abc.def", redacted); self.assertIn("REDACTED", redacted)

    def test_unsafe_html_is_data_not_markup(self):
        result = self.service.submit_message({"message": "<script>alert(1)</script>"})
        self.assertEqual(result.content, "provider-ok")
        script = (Path(__file__).parents[1] / "desktop" / "app.js").read_text(encoding="utf-8")
        self.assertIn("createTextNode", script); self.assertIn("code.textContent", script)

    def test_settings_reject_arbitrary_key(self):
        with self.assertRaises(ValueError): self.service.update_settings({"section": "interface", "key": "shell", "value": "on"})

    def test_theme_switching(self):
        result = self.service.update_settings({"section": "interface", "key": "theme", "value": "light"})
        self.assertEqual(result["settings"]["interface"]["theme"], "light")

    def test_provider_policy_update_uses_command_engine(self):
        self.service.update_settings({"section": "provider", "key": "execution_policy", "value": "local_only"})
        self.assertEqual(self.startup.conversation_manager.records[-1][0], "local only on")

    def test_automatic_provider_policy_updates_validated_session_state(self):
        session = self.startup.conversation_manager.active_session
        session.metadata.update({"local_only": True, "cloud_only": False})
        self.service.update_settings({"section": "provider", "key": "execution_policy", "value": "automatic"})
        self.assertEqual(session.metadata["execution_policy"], "automatic")
        self.assertFalse(session.metadata["local_only"])

    def test_provider_preferences_are_bounded_and_clearable(self):
        session = self.startup.conversation_manager.active_session
        self.service.update_settings({"section": "provider", "key": "model_preference", "value": "llama3.2:1b"})
        self.assertEqual(session.metadata["model_preference"], "llama3.2:1b")
        self.service.update_settings({"section": "provider", "key": "model_preference", "value": ""})
        self.assertNotIn("model_preference", session.metadata)

    def test_graceful_shutdown_endpoint_releases_port(self):
        self.start(); self.post("/api/shutdown", {})
        deadline = time.time() + 5
        while self.service._server is not None and time.time() < deadline:
            time.sleep(0.05)
        sock = socket.socket(); sock.bind(("127.0.0.1", self.port)); sock.close()

    def test_event_stream_connects(self):
        self.start(); self.service._record("test_event", "completed", "r", "Safe event")
        request = urllib.request.Request(self.service.url + "/api/events")
        with urllib.request.urlopen(request, timeout=4) as response:
            packet = response.readline().decode() + response.readline().decode() + response.readline().decode()
        self.assertIn("event: activity", packet)

    def test_port_released_after_shutdown(self):
        self.start(); self.service.stop()
        sock = socket.socket(); sock.bind(("127.0.0.1", self.port)); sock.close()

    def test_frontend_has_accessible_live_region(self):
        html = (Path(__file__).parents[1] / "desktop" / "index.html").read_text(encoding="utf-8")
        self.assertIn('aria-live="polite"', html); self.assertIn('aria-live="assertive"', html); self.assertIn("Shift+Enter", html)

    def test_frontend_does_not_call_providers_or_sapi(self):
        script = (Path(__file__).parents[1] / "desktop" / "app.js").read_text(encoding="utf-8").lower()
        self.assertNotIn("11434", script); self.assertNotIn("ollama/api", script); self.assertNotIn("speechsynthesizer", script)

    def test_no_cors_wildcard(self):
        self.start(); _, headers, _ = self.get("/api/status")
        self.assertIsNone(headers.get("Access-Control-Allow-Origin"))


if __name__ == "__main__":
    unittest.main()
