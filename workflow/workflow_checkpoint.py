"""Workflow checkpoint support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class WorkflowCheckpoint:
    workflow_id: str
    execution_id: str
    execution_state: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def create(self) -> dict[str, Any]:
        return {"workflow_id": self.workflow_id, "execution_id": self.execution_id, "execution_state": self.execution_state, "metadata": self.metadata}
