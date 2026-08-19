import json
import os
import sys
from tempfile import TemporaryDirectory
import unittest
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from config.settings import load_settings
from commands.command_parser import CommandParser
from jarvis.mcp_runtime import (
    LocalStdioTransport,
    MCPPolicy,
    MCPRuntime,
    MCPServerManifest,
    MCPServerState,
    MCPTransportError,
    MCPTransportType,
    MCPTrustState,
    build_mcp_runtime,
    classify_tool,
)


class BrokenTransport:
    def connect(self):
        raise MCPTransportError("mcp_server_start_failed")

    def close(self):
        return None

    def health(self):
        return False


class MCPProtocolIntegrationTests(unittest.TestCase):
    def _transport(self):
        server = Path(__file__).parent / "fixtures" / "mcp_stdio_server.py"
        return LocalStdioTransport(
            sys.executable,
            (str(server),),
            allowed_executables=(sys.executable,),
            timeout=10,
            call_timeout=10,
        )

    def test_official_sdk_stdio_handshake_discovery_resource_and_tool_call(self):
        transport = self._transport()
        runtime = MCPRuntime(policy=MCPPolicy(allow_tool_execution=True), transports={"fixture": transport})
        runtime.registry.register(
            MCPServerManifest(
                "fixture",
                "Fixture",
                MCPTransportType.LOCAL_STDIO,
                executable_ref=Path(sys.executable).name,
                allowed_tools=("search_docs",),
                trust_state=MCPTrustState.TRUSTED_FOR_SPECIFIC_TOOLS,
                enabled=True,
            )
        )
        try:
            result = runtime.discover("fixture")
            self.assertEqual(result.status, "completed", result.error)
            self.assertEqual(runtime.registry.get("fixture").state, MCPServerState.PROTOCOL_READY)
            self.assertIn(("fixture", "search_docs"), runtime.registry.tools)
            self.assertTrue(runtime.registry.resources)
            resource_ref = next(iter(runtime.registry.resources))[1]
            resource = runtime.read_resource("fixture", resource_ref)
            self.assertEqual(resource.status, "completed")
            self.assertIn("fixture content", resource.bounded_summary)
            call = runtime.call("fixture", "search_docs", {"query": "Jarvis"})
            self.assertEqual(call.status, "completed")
            self.assertIn("test-result", call.bounded_summary)
        finally:
            runtime.shutdown()
        self.assertFalse(transport.health())

    def test_prompts_are_not_listed_when_policy_disables_them(self):
        transport = self._transport()
        runtime = MCPRuntime(transports={"fixture": transport})
        runtime.registry.register(MCPServerManifest("fixture", "Fixture", MCPTransportType.LOCAL_STDIO, trust_state=MCPTrustState.TRUSTED_FOR_DISCOVERY, enabled=True))
        try:
            self.assertEqual(runtime.discover("fixture").status, "completed")
            self.assertEqual(runtime.registry.prompts, {})
        finally:
            runtime.shutdown()

    def test_default_policy_discovers_but_never_calls_tools(self):
        transport = self._transport()
        runtime = MCPRuntime(transports={"fixture": transport})
        runtime.registry.register(
            MCPServerManifest(
                "fixture",
                "Fixture",
                MCPTransportType.LOCAL_STDIO,
                allowed_tools=("search_docs",),
                trust_state=MCPTrustState.TRUSTED_FOR_SPECIFIC_TOOLS,
                enabled=True,
            )
        )
        try:
            self.assertEqual(runtime.discover("fixture").status, "completed")
            result = runtime.call("fixture", "search_docs", {"query": "Jarvis"})
            self.assertEqual(result.error, "mcp_execution_disabled")
        finally:
            runtime.shutdown()

    def test_transport_failure_is_normalized(self):
        runtime = MCPRuntime(transports={"broken": BrokenTransport()})
        runtime.registry.register(MCPServerManifest("broken", "Broken", MCPTransportType.LOCAL_STDIO, trust_state=MCPTrustState.TRUSTED_FOR_DISCOVERY, enabled=True))
        result = runtime.discover("broken")
        self.assertEqual(result.error, "mcp_server_start_failed")
        self.assertEqual(runtime.registry.get("broken").state, MCPServerState.ERROR)

    def test_playwright_manifest_loads_discovery_only(self):
        settings = load_settings()
        runtime = build_mcp_runtime(settings.mcp)
        server = runtime.registry.get("playwright")
        self.assertIsNotNone(server)
        self.assertTrue(server.manifest.enabled)
        self.assertEqual(server.manifest.trust_state, MCPTrustState.TRUSTED_FOR_DISCOVERY)
        self.assertEqual(server.manifest.allowed_tools, ())
        self.assertFalse(runtime.policy.allow_tool_execution)
        self.assertFalse(runtime.policy.allow_remote_http)
        self.assertFalse(runtime.policy.allow_installation)
        self.assertIn("playwright", runtime.transports)
        self.assertIn("--isolated", server.manifest.args)
        self.assertIn("--headless", server.manifest.args)

    def test_cached_playwright_resolution_does_not_invoke_npm(self):
        with TemporaryDirectory() as folder:
            cache = Path(folder)
            package = cache / "_npx" / "fixture" / "node_modules" / "@playwright" / "mcp"
            package.mkdir(parents=True)
            cli = package / "cli.js"
            cli.write_text("", encoding="utf-8")
            (package / "package.json").write_text(
                json.dumps({"name": "@playwright/mcp", "bin": {"playwright-mcp": "cli.js"}}),
                encoding="utf-8",
            )
            node = cache / "node.exe"
            node.write_bytes(b"")
            transport = LocalStdioTransport(
                "npx.cmd",
                ("-y", "@playwright/mcp@latest", "--isolated"),
                allowed_executables=("npx.cmd",),
            )
            with patch.dict(os.environ, {"NPM_CONFIG_CACHE": str(cache)}), patch(
                "jarvis.mcp_runtime.transports.shutil.which", return_value=str(node)
            ):
                transport._resolve_effective_command()
            self.assertEqual(transport._effective_executable, str(node))
            self.assertEqual(transport._effective_args, (str(cli), "--isolated"))

    def test_configured_credentials_are_references_not_manifest_values(self):
        values = {item.name: getattr(MCPPolicy(), item.name) for item in fields(MCPPolicy)}
        config = SimpleNamespace(
            **values,
            allowed_executables=("npx.cmd",),
            servers=({
                "server_id": "credentialed",
                "display_name": "Credentialed",
                "transport": "local_stdio",
                "executable_ref": "npx.cmd",
                "required_credentials": ("JARVIS_TEST_MISSING_CREDENTIAL",),
                "trust_state": "trusted_for_discovery",
                "enabled": True,
            },),
        )
        runtime = build_mcp_runtime(config)
        server = runtime.registry.get("credentialed")
        self.assertEqual(server.state, MCPServerState.CREDENTIAL_MISSING)
        self.assertNotIn("credentialed", runtime.transports)

    def test_discover_command_is_parsed_as_structured_cli(self):
        parsed = CommandParser().parse("mcp discover playwright")
        self.assertEqual(parsed.name, "mcp discover")
        self.assertEqual(parsed.arguments, ("playwright",))

    def test_server_destructive_annotation_overrides_read_name_heuristic(self):
        tool = classify_tool(
            "fixture",
            {
                "name": "browser_navigate",
                "description": "Navigate to a URL",
                "annotations": {"readOnlyHint": False, "destructiveHint": True},
            },
            ("browser_navigate",),
        )
        self.assertFalse(tool.read_only)
        self.assertTrue(tool.side_effecting)
        self.assertTrue(tool.approval_required)


if __name__ == "__main__":
    unittest.main()
