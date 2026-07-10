"""Workflow execution context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from workflow.workflow_state import WorkflowState


@dataclass(slots=True)
class WorkflowContext:
    workflow_id: str = field(default_factory=lambda: str(uuid4()))
    execution_id: str = field(default_factory=lambda: str(uuid4()))
    conversation_id: str | None = None
    request_id: str | None = None
    goal_id: str | None = None
    department: str | None = None
    agent: str | None = None
    provider: str | None = None
    execution_strategy: str = "workflow"
    current_step: str | None = None
    completed_steps: tuple[str, ...] = ()
    pending_steps: tuple[str, ...] = ()
    memory_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    task_references: tuple[str, ...] = ()
    plugin_references: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    statistics: dict[str, Any] = field(default_factory=dict)
    state: WorkflowState = WorkflowState.CREATED
