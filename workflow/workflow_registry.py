"""Workflow registry."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow.workflow_builder import WorkflowDefinition


@dataclass(slots=True)
class WorkflowRecord:
    workflow_id: str
    definition: WorkflowDefinition
    enabled: bool = True
    category: str = "general"
    version: str = "0.1"
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowRegistry:
    initialized = True

    def __init__(self) -> None:
        self._records: dict[str, WorkflowRecord] = {}

    def register(self, record: WorkflowRecord) -> None:
        self._records[record.workflow_id] = record

    def unregister(self, workflow_id: str) -> None:
        self._records.pop(workflow_id, None)

    def lookup(self, workflow_id: str) -> WorkflowRecord | None:
        return self._records.get(workflow_id)

    def enable(self, workflow_id: str) -> None:
        self._records[workflow_id].enabled = True

    def disable(self, workflow_id: str) -> None:
        self._records[workflow_id].enabled = False

    def templates(self) -> tuple[WorkflowDefinition, ...]:
        return tuple(record.definition for record in self._records.values())

    def categories(self) -> tuple[str, ...]:
        return tuple(sorted({record.category for record in self._records.values()}))

    def versions(self) -> tuple[str, ...]:
        return tuple(sorted({record.version for record in self._records.values()}))

    def statistics(self) -> dict[str, int]:
        return {"registered_workflows": len(self._records), "enabled_workflows": sum(1 for record in self._records.values() if record.enabled)}

    def metadata(self) -> dict[str, Any]:
        return {workflow_id: record.metadata for workflow_id, record in self._records.items()}
