"""Plugin manifest model and parser."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from plugins.plugin_permissions import PluginPermission


MANIFEST_FILENAME = "plugin.json"


@dataclass(frozen=True, slots=True)
class PluginManifest:
    """Metadata required for every plugin."""

    name: str
    plugin_id: str
    version: str
    author: str
    description: str
    permissions: tuple[PluginPermission, ...] = ()
    dependencies: tuple[str, ...] = ()
    configuration: dict[str, Any] = field(default_factory=dict)
    compatibility_version: str = "0.1"
    entry_point: str = "plugin:Plugin"
    path: Path | None = None

    @classmethod
    def from_file(cls, path: Path) -> "PluginManifest":
        """Load a plugin manifest from JSON."""
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls.from_dict(data, path=path.parent)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        path: Path | None = None,
    ) -> "PluginManifest":
        """Create a manifest from a dictionary."""
        permissions = tuple(
            PluginPermission(value) for value in data.get("permissions", ())
        )
        return cls(
            name=str(data["name"]),
            plugin_id=str(data["id"]),
            version=str(data["version"]),
            author=str(data["author"]),
            description=str(data["description"]),
            permissions=permissions,
            dependencies=tuple(str(value) for value in data.get("dependencies", ())),
            configuration=dict(data.get("configuration", {})),
            compatibility_version=str(data.get("compatibility_version", "0.1")),
            entry_point=str(data.get("entry_point", "plugin:Plugin")),
            path=path,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "name": self.name,
            "id": self.plugin_id,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "permissions": [permission.value for permission in self.permissions],
            "dependencies": list(self.dependencies),
            "configuration": self.configuration,
            "compatibility_version": self.compatibility_version,
            "entry_point": self.entry_point,
        }
