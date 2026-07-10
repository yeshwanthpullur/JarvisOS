"""Tests for Agent Creator generator."""

from __future__ import annotations

import unittest

from agent_creator.blueprint import CustomBlueprint
from agent_creator.generator import AgentGenerator
from agent_creator.manifest import AgentManifest
from agent_creator.template_loader import TemplateLoader


class GeneratorTests(unittest.TestCase):
    """Generator tests."""

    def test_generator_creates_build_plan(self) -> None:
        plan = AgentGenerator().generate(
            CustomBlueprint(),
            TemplateLoader().default_template(),
            AgentManifest("Demo Agent", "Demo", "custom", "custom", "core_agent"),
        )
        self.assertEqual(plan.package_name, "demo_agent")
        self.assertEqual(plan.class_name, "DemoAgentAgent")

    def test_generator_outputs_manifest_json(self) -> None:
        plan = AgentGenerator().generate(
            CustomBlueprint(),
            TemplateLoader().default_template(),
            AgentManifest("Demo", "Demo", "custom", "custom", "core_agent"),
        )
        self.assertIn('"name": "Demo"', plan.generated_files["manifest.json"])

    def test_generator_outputs_readme(self) -> None:
        plan = AgentGenerator().generate(
            CustomBlueprint(),
            TemplateLoader().default_template(),
            AgentManifest("Demo", "Demo", "custom", "custom", "core_agent"),
        )
        self.assertIn("# Demo", plan.generated_files["README.md"])

    def test_generator_rejects_invalid_manifest(self) -> None:
        with self.assertRaises(ValueError):
            AgentGenerator().generate(
                CustomBlueprint(),
                TemplateLoader().default_template(),
                AgentManifest("", "Demo", "custom", "custom", "core_agent"),
            )

    def test_preview_validation_passes(self) -> None:
        generator = AgentGenerator()
        plan = generator.generate(
            CustomBlueprint(),
            TemplateLoader().default_template(),
            AgentManifest("Demo", "Demo", "custom", "custom", "core_agent"),
        )
        self.assertTrue(generator.validate_preview(plan).valid)

    def test_generated_agent_inherits_base_agent_textually(self) -> None:
        plan = AgentGenerator().generate(
            CustomBlueprint(),
            TemplateLoader().default_template(),
            AgentManifest("Demo", "Demo", "custom", "custom", "core_agent"),
        )
        self.assertIn("BaseAgent", plan.generated_files["agent.py"])

