"""Workflow executor architecture."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from workflow.workflow_builder import WorkflowDefinition
from workflow.workflow_context import WorkflowContext
from workflow.workflow_state import WorkflowState


@dataclass(frozen=True, slots=True)
class WorkflowExecutionResult:
    workflow_id: str
    execution_id: str
    state: WorkflowState
    results: dict[str, Any] = field(default_factory=dict)


class WorkflowExecutor:
    initialized = True

    def initialize(self) -> None:
        return None

    def execute(self, definition: WorkflowDefinition, context: WorkflowContext) -> WorkflowExecutionResult:
        return WorkflowExecutionResult(workflow_id=definition.workflow_id, execution_id=context.execution_id, state=WorkflowState.RUNNING)

    def execute_tool(self, tool_manager: Any, plan: Any, context: WorkflowContext) -> Any:
        """Delegate a validated workflow tool step to Tool Intelligence."""
        request = getattr(plan, "request", None)
        if request is None or request.workflow_id not in {None, context.workflow_id}:
            raise ValueError("Tool plan does not belong to this workflow.")
        return tool_manager.execute(plan, executive_approved=True)

    def pause(self) -> None: return None
    def resume(self) -> None: return None
    def cancel(self) -> None: return None
    def restart(self) -> None: return None
    def recover(self) -> None: return None
    def finalize(self) -> None: return None
