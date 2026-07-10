"""Workflow validation."""

from __future__ import annotations

from workflow.workflow_builder import WorkflowDefinition


class WorkflowValidator:
    initialized = True

    def validate(self, definition: WorkflowDefinition) -> tuple[bool, tuple[str, ...]]:
        issues: list[str] = []
        if not definition.name:
            issues.append("Workflow name is required.")
        if not definition.steps:
            issues.append("Workflow steps are required.")
        return (not issues, tuple(issues))
