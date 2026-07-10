"""Tests for Agent Creator templates."""

from __future__ import annotations

import unittest

from agent_creator.blueprint import CustomBlueprint
from agent_creator.manifest import AgentManifest
from agent_creator.template_engine import BaseTemplate, TemplateContext, TemplateEngine
from agent_creator.template_loader import TemplateLoader
from agent_creator.template_registry import TemplateRegistry
from agent_creator.validator import AgentValidator


class TemplateTests(unittest.TestCase):
    """Template engine and registry tests."""

    def test_loader_discovers_default_template(self) -> None:
        self.assertEqual(TemplateLoader().discover()[0].template_id, "core_agent")

    def test_registry_registers_template(self) -> None:
        registry = TemplateRegistry()
        template = TemplateLoader().default_template()
        registry.register(template)
        self.assertIs(registry.require("core_agent"), template)

    def test_registry_rejects_duplicate_template(self) -> None:
        registry = TemplateRegistry()
        template = TemplateLoader().default_template()
        registry.register(template)
        with self.assertRaises(Exception):
            registry.register(template)

    def test_registry_searches_template(self) -> None:
        registry = TemplateRegistry()
        registry.register(TemplateLoader().default_template())
        self.assertEqual(len(registry.search("core")), 1)

    def test_engine_renders_template(self) -> None:
        template = BaseTemplate("t", "Test", files={"agent.py": "class ${class_name}: pass"})
        manifest = AgentManifest("Demo", "Demo", "custom", "custom", "t")
        context = TemplateContext(CustomBlueprint(), manifest, "demo", "DemoAgent")
        rendered = TemplateEngine().render(template, context)
        self.assertIn("DemoAgent", rendered["agent.py"])

    def test_engine_previews_structure(self) -> None:
        template = BaseTemplate("t", "Test", files={"b.py": "", "a.py": ""})
        self.assertEqual(TemplateEngine().preview_structure(template), ("a.py", "b.py"))

    def test_validator_accepts_default_template(self) -> None:
        self.assertTrue(AgentValidator().validate_template(TemplateLoader().default_template()).valid)

    def test_validator_rejects_missing_agent_file(self) -> None:
        template = BaseTemplate("bad", "Bad", files={"__init__.py": ""})
        self.assertFalse(AgentValidator().validate_template(template).valid)

