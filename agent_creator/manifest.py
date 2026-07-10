"""Manifest model for generated agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from agent_creator.capabilities import CreatorCapability
from agent_creator.constants import COMPATIBILITY_VERSION, MANIFEST_VERSION
from agent_creator.permissions import CreatorPermission
from agent_creator.utils import utc_now


@dataclass(frozen=True, slots=True)
class AgentManifest:
    """Provider-independent manifest for a generated agent."""

    name: str
    description: str
    category: str
    blueprint_id: str
    template_id: str
    agent_id: str = field(default_factory=lambda: str(uuid4()))
    version: str = "0.1.0"
    author: str = "JARVIS OS"
    capabilities: tuple[CreatorCapability, ...] = ()
    permissions: tuple[CreatorPermission, ...] = ()
    dependencies: tuple[str, ...] = ()
    configuration: dict[str, Any] = field(default_factory=dict)
    health_metadata: dict[str, Any] = field(default_factory=dict)
    metrics_metadata: dict[str, Any] = field(default_factory=dict)
    compatibility_version: str = COMPATIBILITY_VERSION
    manifest_version: str = MANIFEST_VERSION
    created_at: str = field(default_factory=lambda: utc_now().isoformat())
    updated_at: str = field(default_factory=lambda: utc_now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe manifest dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "category": self.category,
            "blueprint": self.blueprint_id,
            "template": self.template_id,
            "capabilities": [item.value for item in self.capabilities],
            "permissions": [item.value for item in self.permissions],
            "dependencies": list(self.dependencies),
            "configuration": self.configuration,
            "health_metadata": self.health_metadata,
            "metrics_metadata": self.metrics_metadata,
            "compatibility_version": self.compatibility_version,
            "creation_timestamp": self.created_at,
            "modification_timestamp": self.updated_at,
            "manifest_version": self.manifest_version,
        }

