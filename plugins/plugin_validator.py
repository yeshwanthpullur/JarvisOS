"""Plugin validation for manifests and dependencies."""

from __future__ import annotations

import re
from dataclasses import dataclass

from plugins.plugin_manifest import PluginManifest


PLUGIN_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]*$")


@dataclass(frozen=True, slots=True)
class PluginValidationResult:
    """Result of plugin validation."""

    valid: bool
    errors: tuple[str, ...] = ()


class PluginValidator:
    """Validates plugin manifests before loading."""

    def validate_manifest(
        self,
        manifest: PluginManifest,
        available_plugin_ids: tuple[str, ...] = (),
    ) -> PluginValidationResult:
        """Validate required fields, ID shape, path, and dependencies."""
        errors: list[str] = []
        if not manifest.name.strip():
            errors.append("Plugin name is required.")
        if not PLUGIN_ID_PATTERN.match(manifest.plugin_id):
            errors.append("Plugin ID must be lowercase and may contain letters, numbers, dots, dashes, or underscores.")
        if not manifest.version.strip():
            errors.append("Plugin version is required.")
        if not manifest.author.strip():
            errors.append("Plugin author is required.")
        if not manifest.description.strip():
            errors.append("Plugin description is required.")
        if ":" not in manifest.entry_point:
            errors.append("Plugin entry_point must use 'module:ClassName'.")
        if manifest.path is None or not manifest.path.exists():
            errors.append("Plugin path does not exist.")

        available = set(available_plugin_ids)
        missing_dependencies = [
            dependency
            for dependency in manifest.dependencies
            if dependency not in available
        ]
        for dependency in missing_dependencies:
            errors.append(f"Missing plugin dependency: {dependency}")

        return PluginValidationResult(valid=not errors, errors=tuple(errors))
