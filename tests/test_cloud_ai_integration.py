"""Behavioral tests for cloud AI integration."""

from __future__ import annotations

import asyncio
import json
import threading
import unittest
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Iterator
from unittest.mock import patch

from commands import CommandManager
from commands.command_parser import CommandParser
from conversation import ConversationContext, ConversationSession
from config.schema import (
    AgentsConfig,
    AppSettings,
    AutomationConfig,
    BrainConfig,
    DesktopConfig,
    DownloadsConfig,
    GeneralConfig,
    LoggingConfig,
    MemoryConfig,
    MobileConfig,
    ModelsConfig,
    PluginsConfig,
    ProvidersConfig,
    SecurityConfig,
)
from providers import (
    BaseProvider,
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
from providers.base_provider import capabilities_for
from providers.provider_permissions import ProviderPermissionSet
from providers.provider_types import ProviderResponse, ProviderUsage


class _CloudHandler(BaseHTTPRequestHandler):
    models_payload = {
        "data": [
            {
                "id": "cloud-mini",
                "name": "cloud-mini",
                "context_window": 8192,
                "max_tokens": 1024,
            }
        ]
    }

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/v1/models":
            self._send_json(200, self.models_payload)
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
                    "choices": [
                        {
                            "message": {"content": "cloud reply"},
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 5,
                        "completion_tokens": 2,
                        "total_tokens": 7,
                    },
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
def cloud_server() -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _CloudHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


class _StaticProvider(BaseProvider):
    def __init__(self, context: ProviderContext, provider_id: str, local_only: bool) -> None:
        config = ProviderConfig(
            provider_id=provider_id,
            kind=ProviderKind.LOCAL if local_only else ProviderKind.OPENAI,
            enabled=True,
            local_only=local_only,
        )
        context = ProviderContext(
            config=config,
            settings=context.settings,
            permissions=ProviderPermissionSet(),
            logger=context.logger,
        )
        super().__init__(
            context,
            capabilities_for(
                (
                    ProviderCapability.CHAT,
                    ProviderCapability.REASONING,
                    ProviderCapability.CODING,
                    ProviderCapability.STREAMING,
                    ProviderCapability.JSON_MODE,
                )
            ),
        )
        self.enabled = True
        self.initialized = True

    def health_check(self):  # type: ignore[override]
        self.health.mark_success(1.0)
        return self.health

    def list_models(self):
        return (type("Model", (), {"model_id": f"{self.provider_id}-model"})(),)

    async def execute(self, request: ProviderRequest) -> ProviderResponse:
        return ProviderResponse(
            provider_id=self.provider_id,
            model=request.model or f"{self.provider_id}-model",
            content=f"{self.provider_id} reply",
            usage=ProviderUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
            metadata={"provider": self.provider_id},
        )


class CloudAIIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)

    def _settings(self, provider_id: str, kind: ProviderKind, base_url: str, enabled: bool = True) -> AppSettings:
        return AppSettings(
            base_dir=Path(self.tempdir.name),
            general=GeneralConfig(app_name="JARVIS OS", environment="test", debug=False),
            logging=LoggingConfig(level="INFO", log_dir=Path(self.tempdir.name) / "logs", log_file="jarvis.log", max_bytes=1024, backup_count=1),
            memory=MemoryConfig(enabled=True, storage_dir=Path(self.tempdir.name) / "memory", task_store_dir=Path(self.tempdir.name) / "tasks", vector_index_dir=Path(self.tempdir.name) / "vectors"),
            brain=BrainConfig(enabled=True, vault_path=Path(self.tempdir.name) / "vault", vault_name="Jarvis Brain", auto_create_vault=True, daily_note_format="%Y-%m-%d"),
            models=ModelsConfig(default_model="", fallback_model="", allow_local_models=True),
            providers=ProvidersConfig(
                default_provider=provider_id,
                enabled_providers=(provider_id,) if enabled else (),
                timeout_seconds=5,
                max_retries=1,
                track_costs=True,
                definitions={
                    provider_id: {
                        "kind": kind.value,
                        "enabled": enabled,
                        "local_only": kind in {ProviderKind.LOCAL, ProviderKind.OLLAMA, ProviderKind.LM_STUDIO},
                        "base_url": base_url,
                        "api_key_env": "OPENAI_API_KEY" if kind is ProviderKind.OPENAI else "ANTHROPIC_API_KEY",
                        "metadata": {"provider_family": kind.value},
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

    def test_cloud_provider_discovers_models_and_executes(self) -> None:
        with cloud_server() as base_url, patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            settings = self._settings("openai", ProviderKind.OPENAI, base_url)
            manager = ProviderManager(settings.providers, settings=settings)
            stats = manager.initialize()
            self.assertEqual(stats.registered_providers, 1)
            record = manager.registry.require("openai")
            self.assertGreaterEqual(len(record.provider.list_models()), 1)
            response = asyncio.run(
                manager.router.execute_with_failover(
                    ProviderRequest(prompt="Say hello.", goal="Hello", model="cloud-mini", request_id="req-1")
                )
            )
            self.assertEqual(response.provider_id, "openai")
            self.assertEqual(response.model, "cloud-mini")
            self.assertEqual(response.content, "cloud reply")

    def test_router_policy_prefers_and_restricts_candidates(self) -> None:
        local_context = ProviderContext(config=ProviderConfig(provider_id="local", kind=ProviderKind.LOCAL, enabled=True, local_only=True), settings=None, permissions=ProviderPermissionSet(), logger=None)  # type: ignore[arg-type]
        cloud_context = ProviderContext(config=ProviderConfig(provider_id="openai", kind=ProviderKind.OPENAI, enabled=True, local_only=False), settings=None, permissions=ProviderPermissionSet(), logger=None)  # type: ignore[arg-type]
        local = _StaticProvider(local_context, "local", True)
        cloud = _StaticProvider(cloud_context, "openai", False)
        router = ProviderRouter((local, cloud))
        local_only = router.select_provider(ProviderSelectionContext(task_type=ProviderTaskType.CHAT, local_only=True))
        cloud_only = router.select_provider(ProviderSelectionContext(task_type=ProviderTaskType.CHAT, execution_policy="cloud_only"))
        prefer_local = router.select_provider(ProviderSelectionContext(task_type=ProviderTaskType.CHAT, execution_policy="prefer_local"))
        prefer_cloud = router.select_provider(ProviderSelectionContext(task_type=ProviderTaskType.CHAT, execution_policy="prefer_cloud"))
        self.assertEqual(local_only.provider_id, "local")
        self.assertEqual(cloud_only.provider_id, "openai")
        self.assertEqual(prefer_local.provider_id, "local")
        self.assertEqual(prefer_cloud.provider_id, "openai")

    def test_cloud_commands_parse_and_apply(self) -> None:
        parser = CommandParser()
        self.assertEqual(parser.parse("cloud status").name, "cloud status")
        self.assertEqual(parser.parse("cloud use openai cloud-mini").arguments, ("openai", "cloud-mini"))
        self.assertEqual(parser.parse("provider enable openai").name, "provider enable")

    def test_cloud_status_and_selection_commands_work(self) -> None:
        with cloud_server() as base_url, patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            settings = self._settings("openai", ProviderKind.OPENAI, base_url)
            manager = ProviderManager(settings.providers, settings=settings)
            manager.initialize()
            commands = CommandManager()
            commands.initialize()
            conversation = ConversationContext(session=ConversationSession(), provider_manager=manager)
            status = commands.execute("cloud status", conversation)
            self.assertIn("Cloud AI status", status.response)
            use = commands.execute("cloud use openai cloud-mini", conversation)
            self.assertIn("Cloud selection updated", use.response)
            test = commands.execute("cloud test", conversation)
            self.assertIn("Cloud model test succeeded", test.response)
            provider_test = commands.execute("provider test openai", conversation)
            self.assertIn("Provider test completed", provider_test.response)

    def test_provider_enable_and_disable_command_path(self) -> None:
        with cloud_server() as base_url, patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            settings = self._settings("openai", ProviderKind.OPENAI, base_url, enabled=False)
            manager = ProviderManager(settings.providers, settings=settings)
            manager.initialize()
            commands = CommandManager()
            commands.initialize()
            conversation = ConversationContext(session=ConversationSession(), provider_manager=manager)
            enable = commands.execute("provider enable openai", conversation)
            self.assertIn("Provider enabled", enable.response)
            disable = commands.execute("provider disable openai", conversation)
            self.assertIn("Provider disabled", disable.response)

    def test_missing_credentials_do_not_leak_secret(self) -> None:
        with cloud_server() as base_url:
            settings = self._settings("openai", ProviderKind.OPENAI, base_url)
            manager = ProviderManager(settings.providers, settings=settings)
            manager.initialize()
            health = manager.registry.require("openai").provider.health_check()
            self.assertFalse(health.available)
            self.assertNotIn("test-key", health.message)


if __name__ == "__main__":
    unittest.main()
