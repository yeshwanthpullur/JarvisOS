"""Agent structure builder for deterministic generation."""

from __future__ import annotations

from dataclasses import dataclass, field

from agent_creator.blueprint import BaseBlueprint
from agent_creator.manifest import AgentManifest


@dataclass(frozen=True, slots=True)
class AgentBuildPlan:
    """Planned structure for a generated agent package."""

    package_name: str
    class_name: str
    blueprint: BaseBlueprint
    manifest: AgentManifest
    required_modules: tuple[str, ...]
    optional_modules: tuple[str, ...]
    generated_files: dict[str, str] = field(default_factory=dict)


class AgentBuilder:
    """Constructs generation plans from blueprints and manifests."""

    def __init__(self) -> None:
        self.initialized = True

    def build_plan(self, package_name: str, class_name: str, blueprint: BaseBlueprint, manifest: AgentManifest) -> AgentBuildPlan:
        """Build a deterministic agent structure plan."""
        return AgentBuildPlan(
            package_name=package_name,
            class_name=class_name,
            blueprint=blueprint,
            manifest=manifest,
            required_modules=blueprint.required_files,
            optional_modules=blueprint.optional_files,
        )

