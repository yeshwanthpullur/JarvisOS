"""Tests for generated agent manifests."""

from __future__ import annotations

import unittest

from agent_creator.capabilities import CreatorCapability
from agent_creator.manifest import AgentManifest
from agent_creator.permissions import CreatorPermission
from agent_creator.validator import AgentValidator


class ManifestTests(unittest.TestCase):
    """Manifest tests."""

    def test_manifest_serializes(self) -> None:
        manifest = AgentManifest(
            "Demo",
            "Demo",
            "custom",
            "custom",
            "core_agent",
            capabilities=(CreatorCapability.CODING,),
            permissions=(CreatorPermission.MEMORY,),
        )
        data = manifest.to_dict()
        self.assertEqual(data["name"], "Demo")
        self.assertEqual(data["capabilities"], ["coding"])
        self.assertEqual(data["permissions"], ["memory"])

    def test_manifest_has_timestamps(self) -> None:
        manifest = AgentManifest("Demo", "Demo", "custom", "custom", "core_agent")
        self.assertTrue(manifest.created_at)
        self.assertTrue(manifest.updated_at)

    def test_validator_accepts_manifest(self) -> None:
        manifest = AgentManifest("Demo", "Demo", "custom", "custom", "core_agent")
        self.assertTrue(AgentValidator().validate_manifest(manifest).valid)

    def test_validator_rejects_empty_name(self) -> None:
        manifest = AgentManifest("", "Demo", "custom", "custom", "core_agent")
        self.assertFalse(AgentValidator().validate_manifest(manifest).valid)

    def test_manifest_dependencies_serialize(self) -> None:
        manifest = AgentManifest("Demo", "Demo", "custom", "custom", "core_agent", dependencies=("a",))
        self.assertEqual(manifest.to_dict()["dependencies"], ["a"])

