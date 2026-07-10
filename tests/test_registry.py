"""Tests for dynamic agent registry."""

from __future__ import annotations

import unittest

from agent_creator.manifest import AgentManifest
from agent_creator.registry import DynamicAgentRegistry, GeneratedAgentRecord


class RegistryTests(unittest.TestCase):
    """Dynamic registry tests."""

    def make_record(self) -> GeneratedAgentRecord:
        return GeneratedAgentRecord(
            manifest=AgentManifest("Demo", "Demo", "custom", "custom", "core_agent"),
            package_name="demo",
        )

    def test_registry_registers_record(self) -> None:
        registry = DynamicAgentRegistry()
        record = self.make_record()
        registry.register(record)
        self.assertIs(registry.get(record.manifest.agent_id), record)

    def test_registry_enables_record(self) -> None:
        registry = DynamicAgentRegistry()
        record = self.make_record()
        registry.register(record)
        registry.enable(record.manifest.agent_id)
        self.assertTrue(record.enabled)

    def test_registry_disables_record(self) -> None:
        registry = DynamicAgentRegistry()
        record = self.make_record()
        registry.register(record)
        registry.enable(record.manifest.agent_id)
        registry.disable(record.manifest.agent_id)
        self.assertFalse(record.enabled)

    def test_registry_archives_record(self) -> None:
        registry = DynamicAgentRegistry()
        record = self.make_record()
        registry.register(record)
        registry.archive(record.manifest.agent_id)
        self.assertEqual(record.state.value, "archived")

    def test_registry_searches_records(self) -> None:
        registry = DynamicAgentRegistry()
        record = self.make_record()
        registry.register(record)
        self.assertEqual(registry.search("demo"), (record,))

    def test_registry_lists_records(self) -> None:
        registry = DynamicAgentRegistry()
        record = self.make_record()
        registry.register(record)
        self.assertEqual(registry.list_agents(), (record,))

