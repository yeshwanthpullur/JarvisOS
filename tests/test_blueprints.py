"""Tests for Agent Creator blueprints."""

from __future__ import annotations

import unittest

from agents import AgentType
from agent_creator.blueprint import CustomBlueprint, make_blueprint
from agent_creator.blueprint_registry import BlueprintRegistry
from agent_creator.state import BlueprintState
from agent_creator.validator import AgentValidator


class BlueprintTests(unittest.TestCase):
    """Blueprint validation and registry tests."""

    def test_blueprint_serializes(self) -> None:
        data = CustomBlueprint().to_dict()
        self.assertEqual(data["blueprint_id"], "custom")

    def test_blueprint_valid_transition(self) -> None:
        blueprint = CustomBlueprint()
        blueprint.transition_to(BlueprintState.REGISTERED)
        self.assertEqual(blueprint.state, BlueprintState.REGISTERED)

    def test_blueprint_invalid_transition_rejected(self) -> None:
        blueprint = CustomBlueprint()
        with self.assertRaises(ValueError):
            blueprint.transition_to(BlueprintState.INSTALLED)

    def test_registry_registers_blueprint(self) -> None:
        registry = BlueprintRegistry()
        blueprint = CustomBlueprint()
        registry.register(blueprint)
        self.assertIs(registry.get("custom"), blueprint)

    def test_registry_rejects_duplicate(self) -> None:
        registry = BlueprintRegistry()
        registry.register(CustomBlueprint())
        with self.assertRaises(Exception):
            registry.register(CustomBlueprint())

    def test_registry_searches(self) -> None:
        registry = BlueprintRegistry()
        registry.register(make_blueprint("qa", "Quality Blueprint", "engineering", AgentType.CODING))
        self.assertEqual(len(registry.search("quality")), 1)

    def test_registry_filters_category(self) -> None:
        registry = BlueprintRegistry()
        registry.register(make_blueprint("qa", "Quality Blueprint", "engineering", AgentType.CODING))
        self.assertEqual(len(registry.by_category("engineering")), 1)

    def test_validator_accepts_valid_blueprint(self) -> None:
        self.assertTrue(AgentValidator().validate_blueprint(CustomBlueprint()).valid)

    def test_validator_rejects_provider_specific_blueprint(self) -> None:
        blueprint = make_blueprint("bad", "Bad", "bad", AgentType.CUSTOM)
        blueprint.description = "Calls OpenAI directly"
        self.assertFalse(AgentValidator().validate_blueprint(blueprint).valid)

