"""Workflow builder architecture."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow.workflow_context import WorkflowContext
from workflow.workflow_state import WorkflowState


@dataclass(frozen=True, slots=True)
class WorkflowStep:
    name: str
    kind: str = "step"
    dependencies: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    workflow_id: str
    name: str
    type: str
    steps: tuple[WorkflowStep, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowBuilder:
    initialized = True

    def create(self, name: str, steps: tuple[WorkflowStep, ...], workflow_type: str = "sequential") -> WorkflowDefinition:
        return WorkflowDefinition(workflow_id=name.lower().replace(" ", "-"), name=name, type=workflow_type, steps=steps)

    def load(self, definition: WorkflowDefinition) -> WorkflowDefinition:
        return definition

    def clone(self, definition: WorkflowDefinition, workflow_id: str | None = None) -> WorkflowDefinition:
        return WorkflowDefinition(workflow_id=workflow_id or definition.workflow_id, name=definition.name, type=definition.type, steps=definition.steps, metadata=dict(definition.metadata))

    def validate(self, definition: WorkflowDefinition) -> bool:
        return bool(definition.name and definition.steps)

    def optimize(self, definition: WorkflowDefinition) -> WorkflowDefinition:
        return definition

    def serialize(self, definition: WorkflowDefinition) -> dict[str, Any]:
        return {"workflow_id": definition.workflow_id, "name": definition.name, "type": definition.type, "steps": [step.name for step in definition.steps], "metadata": definition.metadata}

    def deserialize(self, payload: dict[str, Any]) -> WorkflowDefinition:
        steps = tuple(WorkflowStep(name=step_name) for step_name in payload.get("steps", ()))
        return WorkflowDefinition(workflow_id=payload.get("workflow_id", ""), name=payload.get("name", ""), type=payload.get("type", "sequential"), steps=steps, metadata=dict(payload.get("metadata", {}) or {}))

    def merge(self, left: WorkflowDefinition, right: WorkflowDefinition) -> WorkflowDefinition:
        return WorkflowDefinition(workflow_id=left.workflow_id, name=left.name, type=left.type, steps=left.steps + right.steps, metadata={**left.metadata, **right.metadata})

    def split(self, definition: WorkflowDefinition) -> tuple[WorkflowDefinition, ...]:
        return tuple(
            WorkflowDefinition(workflow_id=f"{definition.workflow_id}-{index}", name=step.name, type=definition.type, steps=(step,), metadata=dict(definition.metadata))
            for index, step in enumerate(definition.steps, start=1)
        )

    def template_support(self) -> dict[str, Any]:
        return {"supported": True, "states": tuple(state.value for state in WorkflowState)}

