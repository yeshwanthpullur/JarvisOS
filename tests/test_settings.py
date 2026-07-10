"""Tests for configuration loading."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from config.settings import load_settings


class SettingsTests(unittest.TestCase):
    """Configuration loader tests using only the standard library."""

    def test_load_settings_uses_project_defaults(self) -> None:
        settings = load_settings()

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

            settings = load_settings(config_file=config_file)

        self.assertEqual(settings.environment, "test")
        self.assertEqual(settings.log_level, "DEBUG")
        self.assertEqual(settings.providers.enabled_providers, ("local",))

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
