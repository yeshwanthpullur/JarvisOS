"""Tests for Agent Creator orchestration."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_creator import AgentCreator, AgentCreatorContext, AgentManifest


class AgentCreatorTests(unittest.TestCase):
    """Agent Creator startup and orchestration tests."""

    def make_creator(self) -> AgentCreator:
        creator = AgentCreator(AgentCreatorContext(project_root=Path.cwd()))
        creator.initialize()
        return creator

    def test_creator_initializes(self) -> None:
        stats = self.make_creator().statistics()
        self.assertGreaterEqual(stats.registered_blueprints, 10)
        self.assertEqual(stats.registered_templates, 1)

    def test_creator_has_ready_services(self) -> None:
        creator = self.make_creator()
        self.assertTrue(creator.blueprint_registry.initialized)
        self.assertTrue(creator.template_registry.initialized)
        self.assertTrue(creator.generator.initialized)

    def test_creator_preview_generates_files(self) -> None:
        creator = self.make_creator()
        plan = creator.create_preview(
            "custom",
            "core_agent",
            AgentManifest("Demo", "Demo agent", "custom", "custom", "core_agent"),
        )
        self.assertIn("agent.py", plan.generated_files)

    def test_creator_install_metadata(self) -> None:
        creator = self.make_creator()
        with TemporaryDirectory() as temp:
            report = creator.install_generated(
                "custom",
                "core_agent",
                AgentManifest("Demo", "Demo agent", "custom", "custom", "core_agent"),
                Path(temp),
            )
        self.assertEqual(report.status.value, "installed")
        self.assertEqual(creator.statistics().installed_agents, 1)

    def test_creator_departments_initialize(self) -> None:
        stats = self.make_creator().statistics()
        self.assertGreaterEqual(stats.departments, 3)

    def test_creator_health_ready(self) -> None:
        self.assertEqual(self.make_creator().statistics().health_status, "ready")

