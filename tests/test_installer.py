"""Tests for Agent Creator installer and rollback."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_creator.blueprint import CustomBlueprint
from agent_creator.generator import AgentGenerator
from agent_creator.installer import AgentInstaller
from agent_creator.manifest import AgentManifest
from agent_creator.template_loader import TemplateLoader


class InstallerTests(unittest.TestCase):
    """Installer tests."""

    def make_plan(self):
        return AgentGenerator().generate(
            CustomBlueprint(),
            TemplateLoader().default_template(),
            AgentManifest("Demo", "Demo", "custom", "custom", "core_agent"),
        )

    def test_plan_installation_paths(self) -> None:
        paths = AgentInstaller().plan_installation(self.make_plan(), Path("agents_generated"))
        self.assertTrue(any(path.name == "agent.py" for path in paths))

    def test_install_records_registry(self) -> None:
        installer = AgentInstaller()
        report = installer.install(self.make_plan(), Path("agents_generated"))
        self.assertEqual(report.status.value, "installed")
        self.assertEqual(len(installer.registry.list_agents()), 1)

    def test_install_can_write_files(self) -> None:
        installer = AgentInstaller()
        with TemporaryDirectory() as temp:
            report = installer.install(self.make_plan(), Path(temp), write_files=True)
            self.assertTrue((report.target_path / "agent.py").exists())

    def test_uninstall_missing_agent_fails(self) -> None:
        report = AgentInstaller().uninstall("missing")
        self.assertEqual(report.status.value, "failed")

    def test_rollback_plan_created(self) -> None:
        report = AgentInstaller().install(self.make_plan(), Path("agents_generated"))
        self.assertIsNotNone(report.rollback_plan)

    def test_catalog_updated(self) -> None:
        installer = AgentInstaller()
        report = installer.install(self.make_plan(), Path("agents_generated"))
        self.assertIsNotNone(installer.catalog.get(report.agent_id))

