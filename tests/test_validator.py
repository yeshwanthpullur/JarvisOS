"""Tests for Agent Creator validation."""

from __future__ import annotations

import unittest

from agent_creator.dependencies import DependencyResolver
from agent_creator.validator import AgentValidator


class ValidatorTests(unittest.TestCase):
    """Validator and dependency tests."""

    def test_generated_file_validation_accepts_required_files(self) -> None:
        files = {"__init__.py": "", "agent.py": "", "manifest.json": ""}
        self.assertTrue(AgentValidator().validate_generated_files(files).valid)

    def test_generated_file_validation_rejects_missing_manifest(self) -> None:
        files = {"__init__.py": "", "agent.py": ""}
        self.assertFalse(AgentValidator().validate_generated_files(files).valid)

    def test_dependency_resolver_detects_cycle(self) -> None:
        self.assertTrue(DependencyResolver().detect_cycle({"a": ("b",), "b": ("a",)}))

    def test_dependency_resolver_accepts_acyclic_graph(self) -> None:
        self.assertFalse(DependencyResolver().detect_cycle({"a": ("b",), "b": ()}))

    def test_dependency_resolver_reports_missing(self) -> None:
        missing = DependencyResolver().missing_dependencies(("a", "b"), ("a",))
        self.assertEqual(missing, ("b",))

    def test_validator_initialized(self) -> None:
        self.assertTrue(AgentValidator().initialized)

