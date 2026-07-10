"""Agent package generator interfaces."""

from __future__ import annotations

import json
from dataclasses import replace

from agent_creator.builder import AgentBuildPlan, AgentBuilder
from agent_creator.blueprint import BaseBlueprint
from agent_creator.manifest import AgentManifest
from agent_creator.template_engine import BaseTemplate, TemplateContext, TemplateEngine
from agent_creator.utils import class_name_from_identifier, normalize_identifier
from agent_creator.validator import AgentValidator, ValidationReport


class AgentGenerator:
    """Generates complete agent package content without writing files."""

    def __init__(
        self,
        builder: AgentBuilder | None = None,
        template_engine: TemplateEngine | None = None,
        validator: AgentValidator | None = None,
    ) -> None:
        self.builder = builder or AgentBuilder()
        self.template_engine = template_engine or TemplateEngine()
        self.validator = validator or AgentValidator()
        self.initialized = True

    def generate(self, blueprint: BaseBlueprint, template: BaseTemplate, manifest: AgentManifest) -> AgentBuildPlan:
        """Generate a package plan with rendered files."""
        blueprint_report = self.validator.validate_blueprint(blueprint)
        template_report = self.validator.validate_template(template)
        manifest_report = self.validator.validate_manifest(manifest)
        if not (blueprint_report.valid and template_report.valid and manifest_report.valid):
            errors = blueprint_report.errors + template_report.errors + manifest_report.errors
            raise ValueError("; ".join(errors))

        package_name = normalize_identifier(manifest.name)
        class_name = class_name_from_identifier(package_name)
        context = TemplateContext(
            blueprint=blueprint,
            manifest=manifest,
            package_name=package_name,
            class_name=class_name,
        )
        rendered = self.template_engine.render(template, context)
        rendered["manifest.json"] = json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n"
        report = self.validator.validate_generated_files(rendered)
        if not report.valid:
            raise ValueError("; ".join(report.errors))
        plan = self.builder.build_plan(package_name, class_name, blueprint, manifest)
        return replace(plan, generated_files=rendered)

    def validate_preview(self, plan: AgentBuildPlan) -> ValidationReport:
        """Validate a generated preview."""
        return self.validator.validate_generated_files(plan.generated_files)

