"""Workflow engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from workflow.workflow_builder import WorkflowBuilder, WorkflowDefinition
from workflow.workflow_context import WorkflowContext
from workflow.workflow_dispatcher import WorkflowDispatcher
from workflow.workflow_executor import WorkflowExecutor, WorkflowExecutionResult
from workflow.workflow_registry import WorkflowRecord, WorkflowRegistry
from workflow.workflow_scheduler import WorkflowScheduler
from workflow.workflow_state import WorkflowState
from workflow.workflow_validator import WorkflowValidator


@dataclass(frozen=True, slots=True)
class WorkflowExecutionSummary:
    workflow_id: str
    state: WorkflowState
    steps: int
    metadata: dict[str, Any]


class WorkflowEngine:
    initialized = True

    def __init__(
        self,
        registry: WorkflowRegistry | None = None,
        builder: WorkflowBuilder | None = None,
        executor: WorkflowExecutor | None = None,
        dispatcher: WorkflowDispatcher | None = None,
        scheduler: WorkflowScheduler | None = None,
        validator: WorkflowValidator | None = None,
    ) -> None:
        self.registry = registry or WorkflowRegistry()
        self.builder = builder or WorkflowBuilder()
        self.executor = executor or WorkflowExecutor()
        self.dispatcher = dispatcher or WorkflowDispatcher()
        self.scheduler = scheduler or WorkflowScheduler()
        self.validator = validator or WorkflowValidator()

    def create_workflow(self, definition: WorkflowDefinition, category: str = "general") -> WorkflowRecord:
        record = WorkflowRecord(workflow_id=definition.workflow_id, definition=definition, category=category)
        self.registry.register(record)
        return record

    def validate_workflow(self, definition: WorkflowDefinition) -> tuple[bool, tuple[str, ...]]:
        return self.validator.validate(definition)

    def build_execution_graph(self, definition: WorkflowDefinition) -> dict[str, object]:
        return {"workflow_id": definition.workflow_id, "steps": [step.name for step in definition.steps]}

    def create_execution_context(self, workflow_id: str, **metadata: Any) -> WorkflowContext:
        return WorkflowContext(workflow_id=workflow_id, metadata=dict(metadata))

    def execute(self, definition: WorkflowDefinition, context: WorkflowContext) -> WorkflowExecutionResult:
        return self.executor.execute(definition, context)

    def summary(self, definition: WorkflowDefinition, result: WorkflowExecutionResult) -> WorkflowExecutionSummary:
        return WorkflowExecutionSummary(workflow_id=definition.workflow_id, state=result.state, steps=len(definition.steps), metadata={})
