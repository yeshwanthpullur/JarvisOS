"""Validation services for Agent Creator artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent_creator.blueprint import BaseBlueprint
from agent_creator.constants import COMPATIBILITY_VERSION
from agent_creator.manifest import AgentManifest
from agent_creator.template_engine import BaseTemplate


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Validation report for creator artifacts."""

    valid: bool
    errors: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


class AgentValidator:
    """Validates blueprints, templates, manifests, and requests."""

    def __init__(self) -> None:
        self.initialized = True

    def validate_blueprint(self, blueprint: BaseBlueprint) -> ValidationReport:
        """Validate blueprint metadata."""
        errors: list[str] = []
        if not blueprint.blueprint_id:
            errors.append("Blueprint ID is required.")
        if not blueprint.name:
            errors.append("Blueprint name is required.")
        if blueprint.compatibility_version != COMPATIBILITY_VERSION:
            errors.append("Blueprint compatibility version is unsupported.")
        if "openai" in blueprint.description.lower():
            errors.append("Blueprint must remain provider independent.")
        return ValidationReport(valid=not errors, errors=tuple(errors))

    def validate_template(self, template: BaseTemplate) -> ValidationReport:
        """Validate template metadata and required files."""
        errors: list[str] = []
        if not template.template_id:
            errors.append("Template ID is required.")
        if "__init__.py" not in template.files or "agent.py" not in template.files:
            errors.append("Template must include package and agent files.")
        return ValidationReport(valid=not errors, errors=tuple(errors))

    def validate_manifest(self, manifest: AgentManifest) -> ValidationReport:
        """Validate generated agent manifest."""
        errors: list[str] = []
        if not manifest.agent_id:
            errors.append("Agent ID is required.")
        if not manifest.name:
            errors.append("Agent name is required.")
        if manifest.compatibility_version != COMPATIBILITY_VERSION:
            errors.append("Manifest compatibility version is unsupported.")
        return ValidationReport(valid=not errors, errors=tuple(errors))

    def validate_generated_files(self, files: dict[str, str]) -> ValidationReport:
        """Validate generated file output."""
        errors = []
        for required in ("__init__.py", "agent.py", "manifest.json"):
            if required not in files:
                errors.append(f"Generated output missing {required}.")
        return ValidationReport(valid=not errors, errors=tuple(errors))

