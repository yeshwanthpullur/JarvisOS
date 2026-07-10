"""Tests for Agent Creator catalog and security/audit shells."""

from __future__ import annotations

import unittest

from agent_creator.audit import AuditManager
from agent_creator.catalog import AgentCatalog, CatalogEntry
from agent_creator.department import DepartmentManager
from agent_creator.manifest import AgentManifest
from agent_creator.policy import PolicyEngine
from agent_creator.security import SecurityManager, SecurityPolicy


class CatalogTests(unittest.TestCase):
    """Catalog tests."""

    def make_entry(self) -> CatalogEntry:
        manifest = AgentManifest("Demo", "Demo", "custom", "custom", "core_agent")
        return CatalogEntry(manifest, "core_agent", "custom")

    def test_catalog_adds_entry(self) -> None:
        catalog = AgentCatalog()
        entry = self.make_entry()
        catalog.add(entry)
        self.assertIs(catalog.get(entry.manifest.agent_id), entry)

    def test_catalog_searches_entry(self) -> None:
        catalog = AgentCatalog()
        entry = self.make_entry()
        catalog.add(entry)
        self.assertEqual(catalog.search("demo"), (entry,))

    def test_policy_engine_loads_policy(self) -> None:
        engine = PolicyEngine()
        policy = SecurityPolicy()
        engine.load_policy(policy)
        self.assertEqual(engine.list_policies(), (policy,))

    def test_security_manager_validates_policy(self) -> None:
        self.assertTrue(SecurityManager().validate_policy(SecurityPolicy()))

    def test_audit_manager_records_action(self) -> None:
        manager = AuditManager()
        record = manager.record("create", "agent")
        self.assertEqual(manager.list_records(), (record,))

    def test_department_manager_initializes_defaults(self) -> None:
        manager = DepartmentManager()
        manager.initialize_defaults()
        self.assertGreaterEqual(len(manager.registry.list_departments()), 3)

