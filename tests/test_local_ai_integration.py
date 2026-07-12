"""Behavioral tests for local AI integration."""

from __future__ import annotations

import asyncio
import json
import threading
import unittest
import urllib.request
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator

from commands import CommandManager
from conversation import ConversationContext, ConversationSession
from core.startup_manager import StartupManager
from provider_execution import ExecutionManager, ProviderExecutionContext, ProviderExecutionRequest, ProviderExecutionRegistry
from providers import (
    LocalProvider,
    ModelInfo,
    OllamaProvider,
    ProviderCapability,
    ProviderConfig,
    ProviderContext,
    ProviderKind,
    ProviderManager,
    ProviderRequest,
    ProviderRouter,
    ProviderSelectionContext,
    ProviderTaskType,
)
from providers.provider_factory import ProviderFactory
from task_intelligence.task_manager import TaskIntelligenceManager


class _LocalAIHandler(BaseHTTPRequestHandler):
    models_payload = {
        "data": [
            {
                "id": "local-small",
                "name": "local-small",
                "context_window": 4096,
                "max_tokens": 1024,
            }
        ]
    }
    ollama_models_payload = {
        "models": [
            {
                "name": "ollama-mini",
                "context_length": 8192,
            }
        ]
    }
    completion_text = "local reply"

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            self._send_json(200, self.models_payload)
            return
        if self.path == "/api/tags":
            self._send_json(200, self.ollama_models_payload)
            return
        self._send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b"{}"
        payload = json.loads(body.decode("utf-8") or "{}")
        if self.path == "/v1/chat/completions":
            self._send_json(
                200,
                {
                    "choices": [{"message": {"content": self.completion_text}, "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 4, "completion_tokens": 2, "total_tokens": 6},
                    "echo": payload,
                },
            )
            return
        if self.path == "/api/chat":
            self._send_json(
                200,
                {
                    "message": {"content": self.completion_text},
                    "done_reason": "stop",
                    "usage": {"prompt_eval_count": 4, "eval_count": 2, "total_tokens": 6},
                    "echo": payload,
                },
            )
            return
        self._send_json(404, {"error": "not found"})

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return

    def _send_json(self, status: int, payload: dict[str, object]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


@contextmanager
def local_ai_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _LocalAIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class LocalAIIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)

    def _providers_config(self, provider_id: str, base_url: str, kind: ProviderKind) -> ProviderManager:
        from config.schema import AppSettings, GeneralConfig, LoggingConfig, MemoryConfig, BrainConfig, ModelsConfig, ProvidersConfig, AgentsConfig, PluginsConfig, DownloadsConfig, AutomationConfig, SecurityConfig, DesktopConfig, MobileConfig

        settings = AppSettings(
            base_dir=Path(self.tempdir.name),
            general=GeneralConfig(app_name="JARVIS OS", environment="test", debug=False),
            logging=LoggingConfig(level="INFO", log_dir=Path(self.tempdir.name) / "logs", log_file="jarvis.log", max_bytes=1024, backup_count=1),
            memory=MemoryConfig(enabled=True, storage_dir=Path(self.tempdir.name) / "memory", task_store_dir=Path(self.tempdir.name) / "tasks", vector_index_dir=Path(self.tempdir.name) / "vectors"),
            brain=BrainConfig(enabled=True, vault_path=Path(self.tempdir.name) / "vault", vault_name="Jarvis Brain", auto_create_vault=True, daily_note_format="%Y-%m-%d"),
            models=ModelsConfig(default_model="", fallback_model="", allow_local_models=True),
            providers=ProvidersConfig(
                default_provider=provider_id,
                enabled_providers=(provider_id,),
                timeout_seconds=5,
                max_retries=1,
                track_costs=True,
                definitions={
                    provider_id: {
                        "kind": kind.value,
                        "enabled": True,
                        "local_only": True,
                        "base_url": base_url,
                        "metadata": {"local": True},
                    }
                },
            ),
            agents=AgentsConfig(enabled=True, max_concurrent_agents=2, workspace_dir=Path(self.tempdir.name) / "agents"),
            plugins=PluginsConfig(enabled=False, plugin_dir=Path(self.tempdir.name) / "plugins", allow_user_plugins=False, auto_discover=False, auto_enable=False, compatibility_version="0.1"),
            downloads=DownloadsConfig(download_dir=Path(self.tempdir.name) / "downloads", max_concurrent_downloads=1, verify_integrity=True),
            automation=AutomationConfig(enabled=False, queue_dir=Path(self.tempdir.name) / "automation", max_concurrent_jobs=1),
            security=SecurityConfig(secrets_dir=Path(self.tempdir.name) / "secrets", allow_shell_execution=False, allow_network_access=False, require_confirmation_for_installers=True),
            desktop=DesktopConfig(enabled=False, platform="windows", downloads_folder=None),
            mobile=MobileConfig(enabled=False, api_enabled=False),
        )
        return ProviderManager(settings.providers, settings=settings)

    def test_local_provider_discovers_models_and_executes(self) -> None:
        with local_ai_server() as base_url:
            manager = self._providers_config("ollama", base_url, ProviderKind.OLLAMA)
            stats = manager.initialize()
            self.assertEqual(stats.registered_providers, 1)
            record = manager.registry.require("ollama")
            self.assertGreaterEqual(len(record.provider.list_models()), 1)
            result = asyncio.run(
                manager.router.execute_with_failover(
                    ProviderRequest(
                        prompt="Say hello.",
                        goal="Hello",
                        model="ollama-mini",
                        request_id="req-1",
                        local_only=True,
                    )
                )
            )
            self.assertEqual(result.content, "local reply")
            self.assertEqual(result.provider_id, "ollama")
            self.assertEqual(result.model, "ollama-mini")

    def test_local_provider_health_reports_available(self) -> None:
        with local_ai_server() as base_url:
            provider = ProviderFactory().create(
                ProviderConfig(provider_id="local", kind=ProviderKind.LOCAL, enabled=True, local_only=True, base_url=base_url)
            )
            provider.initialize()
            health = provider.health_check()
            self.assertTrue(health.available)
            self.assertGreaterEqual(len(provider.list_models()), 1)

    def test_local_provider_reports_missing_model_truthfully(self) -> None:
        with local_ai_server() as base_url:
            provider = ProviderFactory().create(
                ProviderConfig(provider_id="local", kind=ProviderKind.LOCAL, enabled=True, local_only=True, base_url=base_url)
            )
            provider.initialize()
            response = provider.chat(ProviderRequest(prompt="hello", goal="hello", model="missing", local_only=True))
            self.assertIn("Model missing", response.error or "")

    def test_unreachable_runtime_is_unavailable(self) -> None:
        provider = ProviderFactory().create(
            ProviderConfig(provider_id="local", kind=ProviderKind.LOCAL, enabled=True, local_only=True, base_url="http://127.0.0.1:1")
        )
        provider.initialize()
        health = provider.health_check()
        self.assertFalse(health.available)

    def test_router_local_only_prefers_local_provider(self) -> None:
        with local_ai_server() as base_url:
            manager = self._providers_config("local", base_url, ProviderKind.LOCAL)
            manager.initialize()
            selected = manager.router.select_provider(
                ProviderSelectionContext(
                    goal="Test",
                    task_type=ProviderTaskType.CHAT,
                    local_only=True,
                )
            )
            self.assertEqual(selected.provider_id, "local")

    def test_execution_manager_routes_through_router(self) -> None:
        with local_ai_server() as base_url:
            manager = self._providers_config("ollama", base_url, ProviderKind.OLLAMA)
            manager.initialize()
            execution_manager = ExecutionManager(
                context=ProviderExecutionContext(provider_manager=manager, provider_router=manager.router)
            )
            execution_manager.initialize()
            response = execution_manager.execute_through_provider_router(
                ProviderExecutionRequest(intent="chat", goal="Say hello", metadata={"local_only": True, "task_type": "chat"})
            )
            self.assertTrue(response.success)
            self.assertEqual(response.provider, "ollama")

    def test_local_status_command_reports_models(self) -> None:
        with local_ai_server() as base_url:
            manager = self._providers_config("local", base_url, ProviderKind.LOCAL)
            manager.initialize()
            commands = CommandManager()
            commands.initialize()
            conversation = ConversationContext(
                session=ConversationSession(),
                provider_manager=manager,
                metadata={},
            )
            response = commands.execute("local status", conversation)
            self.assertIn("Local AI status", response.response)
            self.assertNotIn("unavailable", response.response.lower())

    def test_provider_manager_falls_back_to_metadata(self) -> None:
        with local_ai_server() as base_url:
            manager = self._providers_config("local", base_url, ProviderKind.LOCAL)
            manager.initialize()
            commands = CommandManager()
            commands.initialize()
            conversation = ConversationContext(
                session=ConversationSession(),
                metadata={"provider_manager": manager},
            )
            response = commands.execute("local status", conversation)
            self.assertIn("Local AI status", response.response)

    def test_local_models_command_lists_models(self) -> None:
        with local_ai_server() as base_url:
            manager = self._providers_config("ollama", base_url, ProviderKind.OLLAMA)
            manager.initialize()
            commands = CommandManager()
            commands.initialize()
            conversation = ConversationContext(
                session=ConversationSession(),
                provider_manager=manager,
            )
            response = commands.execute("local models", conversation)
            self.assertIn("ollama:ollama-mini", response.response)

    def test_local_use_command_parses_and_applies_model(self) -> None:
        with local_ai_server() as base_url:
            manager = self._providers_config("ollama", base_url, ProviderKind.OLLAMA)
            manager.initialize()
            commands = CommandManager()
            commands.initialize()
            conversation = ConversationContext(
                session=ConversationSession(),
                provider_manager=manager,
            )
            response = commands.execute("local use ollama-mini", conversation)
            self.assertIn("Local model selected", response.response)
            self.assertEqual(conversation.session.metadata.get("local_model"), "ollama-mini")
            self.assertEqual(conversation.session.metadata.get("local_provider"), "ollama")

    def test_local_test_uses_model_id(self) -> None:
        with local_ai_server() as base_url:
            manager = self._providers_config("ollama", base_url, ProviderKind.OLLAMA)
            manager.initialize()
            commands = CommandManager()
            commands.initialize()
            conversation = ConversationContext(
                session=ConversationSession(),
                provider_manager=manager,
            )
            response = commands.execute("local test", conversation)
            self.assertIn("Local model test succeeded", response.response)

    def test_real_ollama_command_path_uses_installed_model(self) -> None:
        try:
            models = json.loads(
                urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=5).read().decode("utf-8")
            ).get("models", [])
        except Exception as exc:  # pragma: no cover - environment dependent
            self.skipTest(f"Ollama runtime unavailable: {exc}")
        if not any(model.get("name") == "llama3.2:1b" for model in models):
            self.skipTest("llama3.2:1b is not installed in this environment.")
        manager = self._providers_config("ollama", "http://127.0.0.1:11434", ProviderKind.OLLAMA)
        manager.initialize()
        commands = CommandManager()
        commands.initialize()
        conversation = ConversationContext(
            session=ConversationSession(),
            provider_manager=manager,
        )
        use_response = commands.execute("local use llama3.2:1b", conversation)
        self.assertIn("Local model selected", use_response.response)
        test_response = commands.execute("local test", conversation)
        self.assertIn("Local model test succeeded", test_response.response)

    def test_startup_includes_local_ai_framework(self) -> None:
        startup = StartupManager()
        startup.start()
        try:
            self.assertIsNotNone(startup.provider_manager)
            self.assertIn("local_ai", {result.name for result in startup.health_results})
        finally:
            startup.shutdown()

    def test_command_parser_recognizes_local_use(self) -> None:
        from commands.command_parser import CommandParser

        parsed = CommandParser().parse("local use llama3.2:1b")
        self.assertEqual(parsed.name, "local use")
        self.assertEqual(parsed.arguments, ("llama3.2:1b",))

    def test_existing_local_commands_still_parse(self) -> None:
        from commands.command_parser import CommandParser

        parser = CommandParser()
        self.assertEqual(parser.parse("local status").name, "local status")
        self.assertEqual(parser.parse("local providers").name, "local providers")
        self.assertEqual(parser.parse("local models").name, "local models")
        self.assertEqual(parser.parse("local refresh").name, "local refresh")
        self.assertEqual(parser.parse("local test").name, "local test")
        self.assertEqual(parser.parse("local only on").name, "local only on")
        self.assertEqual(parser.parse("local only off").name, "local only off")

    def test_disabled_local_only_mode_is_truthful(self) -> None:
        with local_ai_server() as base_url:
            manager = self._providers_config("local", base_url, ProviderKind.LOCAL)
            manager.initialize()
            response = asyncio.run(
                manager.router.execute_with_failover(
                    ProviderRequest(prompt="hello", goal="hello", model="local-small", local_only=True)
                )
            )
            self.assertEqual(response.provider_id, "local")
