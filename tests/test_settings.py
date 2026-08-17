"""Tests for configuration loading."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from config.settings import load_settings


class SettingsTests(unittest.TestCase):
    """Configuration loader tests using only the standard library."""

    def test_load_settings_uses_project_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                config_file=Path(directory) / "missing-config.yaml",
                env_file=Path(directory) / "missing.env",
            )

        self.assertEqual(settings.app_name, "JARVIS OS")
        self.assertEqual(settings.environment, "development")
        self.assertFalse(settings.debug)
        self.assertEqual(settings.log_level, "INFO")
        self.assertEqual(settings.providers.timeout_seconds, 30)
        self.assertFalse(settings.security.allow_shell_execution)

    def test_load_settings_supports_yaml_overrides(self) -> None:
        self._skip_without_yaml()

        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "config.yaml"
            config_file.write_text(
                """
general:
  environment: test
logging:
  level: DEBUG
providers:
  enabled_providers:
    - local
""",
                encoding="utf-8",
            )

            settings = load_settings(
                config_file=config_file,
                env_file=Path(directory) / "missing.env",
            )

        self.assertEqual(settings.environment, "test")
        self.assertEqual(settings.log_level, "DEBUG")
        self.assertEqual(settings.providers.enabled_providers, ("local",))

    def test_load_settings_applies_later_phase_yaml_overrides(self) -> None:
        self._skip_without_yaml()

        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "config.yaml"
            config_file.write_text(
                """
research:
  max_sources_standard: 7
knowledge:
  max_results: 3
orchestrator:
  max_parallel_agents: 1
documents:
  max_extract_chars: 1234
browser:
  max_history_items: 9
scheduler:
  minimum_cadence_minutes: 120
communication:
  external_max_message_chars: 2048
adapters:
  max_plan_steps: 4
models_advanced:
  max_providers_listed: 12
evaluation:
  max_cases_per_suite: 50
release_readiness:
  max_gates: 40
execution:
  allow_file_writes: false
approvals:
  default_ttl_seconds: 600
broker:
  allow_actual_execution: false
""",
                encoding="utf-8",
            )

            settings = load_settings(
                config_file=config_file,
                env_file=Path(directory) / "missing.env",
            )

        self.assertEqual(settings.research.max_sources_standard, 7)
        self.assertEqual(settings.knowledge_index.max_results, 3)
        self.assertEqual(settings.orchestrator.max_parallel_agents, 1)
        self.assertEqual(settings.documents.max_extract_chars, 1234)
        self.assertEqual(settings.browser.max_history_items, 9)
        self.assertEqual(settings.scheduler.minimum_cadence_minutes, 120)
        self.assertEqual(settings.communication.external_max_message_chars, 2048)
        self.assertEqual(settings.adapters.max_plan_steps, 4)
        self.assertEqual(settings.advanced_models.max_providers_listed, 12)
        self.assertEqual(settings.evaluation.max_cases_per_suite, 50)
        self.assertEqual(settings.release_readiness.max_gates, 40)
        self.assertFalse(settings.execution.allow_file_writes)
        self.assertEqual(settings.approvals.default_ttl_seconds, 600)
        self.assertFalse(settings.broker.allow_actual_execution)

    def test_reliability_defaults_do_not_claim_automatic_self_healing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = load_settings(
                config_file=Path(directory) / "missing-config.yaml",
                env_file=Path(directory) / "missing.env",
            )

        self.assertFalse(settings.reliability.enable_self_healing)

    def test_load_settings_env_file_overrides_yaml(self) -> None:
        self._skip_without_yaml()

        with tempfile.TemporaryDirectory() as directory:
            config_file = Path(directory) / "config.yaml"
            env_file = Path(directory) / ".env"

            config_file.write_text(
                """
general:
  environment: yaml
""",
                encoding="utf-8",
            )
            env_file.write_text("JARVIS_ENVIRONMENT=env\n", encoding="utf-8")

            settings = load_settings(config_file=config_file, env_file=env_file)

        self.assertEqual(settings.environment, "env")

    def _skip_without_yaml(self) -> None:
        try:
            import yaml  # noqa: F401
        except ImportError:
            self.skipTest("PyYAML is not installed.")


if __name__ == "__main__":
    unittest.main()
