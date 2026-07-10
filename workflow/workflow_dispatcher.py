"""Workflow dispatcher."""

from __future__ import annotations

from workflow.workflow_builder import WorkflowDefinition, WorkflowStep
from workflow.workflow_context import WorkflowContext


class WorkflowDispatcher:
    initialized = True

    def dispatch_step(self, step: WorkflowStep, context: WorkflowContext) -> dict[str, object]:
        return {"step": step.name, "workflow_id": context.workflow_id}
