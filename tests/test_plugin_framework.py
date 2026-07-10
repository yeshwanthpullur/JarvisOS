"""Tests for the JARVIS OS Plugin Framework."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from plugins import (
    BasePlugin,
    PluginLifecycleState,
    PluginManager,
    PluginManifest,
    PluginPermission,
    PluginValidator,
)


class PluginFrameworkTests(unittest.TestCase):
    """Plugin discovery, lifecycle, dependency, and permission tests."""

    def test_discover_validate_load_initialize_and_enable_plugin(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin_root = Path(directory)
            self._write_plugin(plugin_root / "hello", plugin_id="hello")
            manager = PluginManager(plugin_root)

            stats = manager.initialize()
            record = manager.registry.require("hello")

            self.assertEqual(stats.loaded_plugins, 1)
            self.assertEqual(stats.enabled_plugins, 1)
            self.assertEqual(record.state, PluginLifecycleState.ENABLED)
            self.assertIsInstance(record.instance, BasePlugin)

    def test_missing_dependency_marks_plugin_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin_root = Path(directory)
            self._write_plugin(
                plugin_root / "dependent",
                plugin_id="dependent",
                dependencies=("missing",),
            )
            manager = PluginManager(plugin_root)

            stats = manager.initialize()
            record = manager.registry.require("dependent")

            self.assertEqual(stats.invalid_plugins, 1)
            self.assertEqual(record.state, PluginLifecycleState.INVALID)
            self.assertIn("Missing plugin dependency: missing", record.errors)

    def test_dependency_load_order_supports_plugin_dependencies(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin_root = Path(directory)
            self._write_plugin(plugin_root / "base", plugin_id="base")
            self._write_plugin(
                plugin_root / "child",
                plugin_id="child",
                dependencies=("base",),
            )
            manager = PluginManager(plugin_root)

            stats = manager.initialize()

            self.assertEqual(stats.loaded_plugins, 2)
            self.assertEqual(manager.registry.require("base").state, PluginLifecycleState.ENABLED)
            self.assertEqual(manager.registry.require("child").state, PluginLifecycleState.ENABLED)

    def test_permission_checks_are_enforced_by_context(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin_root = Path(directory)
            self._write_plugin(
                plugin_root / "permissioned",
                plugin_id="permissioned",
                permissions=("memory",),
                extra_code=(
                    "\n    def check(self):\n"
                    "        self.context.require_permission(PluginPermission.MEMORY)\n"
                    "        return True\n"
                    "\n    def denied(self):\n"
                    "        self.context.require_permission(PluginPermission.CAMERA)\n"
                ),
            )
            manager = PluginManager(plugin_root)
            manager.initialize()
            plugin = manager.registry.require("permissioned").instance
            self.assertIsNotNone(plugin)

            self.assertTrue(plugin.check())  # type: ignore[union-attr]
            with self.assertRaises(PermissionError):
                plugin.denied()  # type: ignore[union-attr]

    def test_disable_reload_unload_and_remove_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            plugin_root = Path(directory)
            self._write_plugin(plugin_root / "hello", plugin_id="hello")
            manager = PluginManager(plugin_root)
            manager.initialize()

            self.assertEqual(
                manager.disable_plugin("hello").state,
                PluginLifecycleState.DISABLED,
            )
            self.assertEqual(
                manager.reload_plugin("hello").state,
                PluginLifecycleState.ENABLED,
            )
            self.assertEqual(
                manager.unload_plugin("hello").state,
                PluginLifecycleState.UNLOADED,
            )
            self.assertEqual(
                manager.remove_plugin("hello").state,
                PluginLifecycleState.REMOVED,
            )

    def test_validator_rejects_invalid_plugin_id(self) -> None:
        manifest = PluginManifest.from_dict(
            {
                "name": "Bad",
                "id": "Bad Plugin",
                "version": "0.1.0",
                "author": "Test",
                "description": "Invalid ID",
                "permissions": [],
                "dependencies": [],
                "configuration": {},
                "entry_point": "plugin:BadPlugin",
            },
            path=Path("."),
        )

        result = PluginValidator().validate_manifest(manifest)

        self.assertFalse(result.valid)
        self.assertTrue(any("Plugin ID" in error for error in result.errors))

    def _write_plugin(
        self,
        plugin_dir: Path,
        plugin_id: str,
        dependencies: tuple[str, ...] = (),
        permissions: tuple[str, ...] = ("notifications",),
        extra_code: str = "",
    ) -> None:
        plugin_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "name": plugin_id.title(),
            "id": plugin_id,
            "version": "0.1.0",
            "author": "Test",
            "description": "Test plugin",
            "permissions": list(permissions),
            "dependencies": list(dependencies),
            "configuration": {"message": "Plugin Loaded Successfully"},
            "compatibility_version": "0.1",
            "entry_point": "plugin:TestPlugin",
        }
        (plugin_dir / "plugin.json").write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )
        (plugin_dir / "plugin.py").write_text(
            "from plugins import BasePlugin, PluginPermission\n\n"
            "class TestPlugin(BasePlugin):\n"
            "    def on_load(self):\n"
            "        self.context.logger.info('test_plugin_loaded')\n"
            f"{extra_code}\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
