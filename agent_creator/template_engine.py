"""Deterministic template rendering for generated agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from string import Template
from typing import Mapping

from agent_creator.blueprint import BaseBlueprint
from agent_creator.manifest import AgentManifest


@dataclass(frozen=True, slots=True)
class BaseTemplate:
    """Template metadata and deterministic file templates."""

    template_id: str
    name: str
    version: str = "0.1.0"
    author: str = "JARVIS OS"
    description: str = ""
    files: Mapping[str, str] = field(default_factory=dict)
    compatibility_version: str = "0.1"
    tags: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class TemplateContext:
    """Context supplied to template rendering."""

    blueprint: BaseBlueprint
    manifest: AgentManifest
    package_name: str
    class_name: str
    configuration: Mapping[str, object] = field(default_factory=dict)


class TemplateEngine:
    """Render templates without AI, randomness, or external services."""

    def __init__(self) -> None:
        self.initialized = True

    def render(self, template: BaseTemplate, context: TemplateContext) -> dict[str, str]:
        """Render all files in a template."""
        values = {
            "agent_id": context.manifest.agent_id,
            "name": context.manifest.name,
            "description": context.manifest.description,
            "version": context.manifest.version,
            "author": context.manifest.author,
            "category": context.manifest.category,
            "blueprint_id": context.blueprint.blueprint_id,
            "template_id": context.manifest.template_id,
            "package_name": context.package_name,
            "class_name": context.class_name,
        }
        return {
            path: Template(content).safe_substitute(values)
            for path, content in template.files.items()
        }

    def preview_structure(self, template: BaseTemplate) -> tuple[str, ...]:
        """Return file paths that would be generated."""
        return tuple(sorted(template.files))

