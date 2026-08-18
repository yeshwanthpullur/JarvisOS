"""Prompt 88-89 environment isolation and local model boundary tests."""

from __future__ import annotations

from dataclasses import replace
import unittest
from unittest.mock import patch

from commands import CommandManager
from jarvis.phase6 import EnvironmentStatus, LocalModelCatalog, Phase6Runtime, build_tool_environment_registry
from jarvis.phase6.models import ModelRecord


class ToolEnvironmentTests(unittest.TestCase):
    def test_registry_is_unique_bounded_and_non_authoritative(self) -> None:
        registry = build_tool_environment_registry()
        records = registry.list()
        self.assertEqual(len(records), len({item.tool_id for item in records}))
        self.assertLessEqual(len(records), 32)
        self.assertFalse(registry.summary()["execution_authority"])
        self.assertTrue(all(not item.enabled for item in records))

    def test_duplicate_tool_rejected(self) -> None:
        registry = build_tool_environment_registry()
        with self.assertRaisesRegex(ValueError, "duplicate_tool_environment"):
            registry.register(registry.list()[0])

    @patch("jarvis.phase6.environment.metadata.version", side_effect=Exception("import failed"))
    def test_failed_detection_is_safe(self, _version) -> None:
        registry = build_tool_environment_registry()
        record = registry.inspect("playwright")
        self.assertIn(record.health_status, {EnvironmentStatus.MISSING, EnvironmentStatus.DEGRADED, EnvironmentStatus.INCOMPATIBLE})
        self.assertTrue(record.last_error)

    def test_permission_profiles_do_not_grant_writes(self) -> None:
        registry = build_tool_environment_registry()
        for tool_id in ("aider", "open_interpreter", "browser_use"):
            record = registry.get(tool_id)
            self.assertIsNotNone(record)
            self.assertNotIn("write_files", record.permission_profile)
            self.assertNotIn("execute_commands", record.permission_profile)

    def test_dependency_audit_is_passive_and_bounded(self) -> None:
        audit = build_tool_environment_registry().audit(run_pip_check=False)
        self.assertEqual(audit.pip_check_status, "not_run")
        self.assertLessEqual(len(audit.warnings), 12)
        self.assertTrue(audit.python_version)


class LocalModelTests(unittest.TestCase):
    @patch("jarvis.phase6.models.shutil.which", return_value=None)
    def test_ollama_missing_is_truthful(self, _which) -> None:
        catalog = LocalModelCatalog()
        provider = catalog.provider("ollama")
        self.assertFalse(provider.detected)
        self.assertFalse(provider.healthy)
        self.assertFalse(catalog.summary()["cloud_fallback"])

    def test_role_selection_requires_available_compatible_model(self) -> None:
        catalog = LocalModelCatalog()
        catalog._models["local"] = ModelRecord("local", "local", "ollama", "ollama", ("general_chat",), available=True, healthy=True)
        self.assertTrue(catalog.select("general_chat", "local"))
        self.assertFalse(catalog.select("vision", "local"))
        self.assertEqual(catalog.route("general_chat").model_id, "local")

    def test_unknown_role_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown_model_role"):
            LocalModelCatalog().select("admin", "missing")

    def test_cloud_gateway_disabled_by_default(self) -> None:
        provider = LocalModelCatalog().provider("litellm")
        self.assertFalse(provider.enabled)
        self.assertFalse(provider.policy_allowed)


class Phase6CommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = CommandManager()
        self.manager.initialize()

    def test_environment_and_tool_commands_are_bounded(self) -> None:
        for command in ("environment status", "environment audit", "tool status", "tool environments", "tool inspect aider"):
            output = self.manager.execute(command).response
            self.assertNotIn("Unknown command", output)
            self.assertLess(len(output), 7000)
            self.assertNotIn("C:\\Users\\", output)

    def test_model_commands_do_not_download_or_execute(self) -> None:
        for command in ("model list", "model roles", "model inspect missing", "model test missing"):
            output = self.manager.execute(command).response
            self.assertNotIn("Unknown command", output)
            self.assertLess(len(output), 6000)
        self.assertIn("No model was downloaded", self.manager.execute("model test missing").response)

    def test_unknown_phase6_subcommand_returns_help(self) -> None:
        output = self.manager.execute("environment destroy").response
        self.assertIn("Unknown environment command", output)


if __name__ == "__main__":
    unittest.main()
