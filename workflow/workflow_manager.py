"""Workflow manager."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from workflow.workflow_builder import WorkflowBuilder, WorkflowDefinition
from workflow.workflow_checkpoint import WorkflowCheckpoint
from workflow.workflow_context import WorkflowContext
from workflow.workflow_diagnostics import WorkflowDiagnostics
from workflow.workflow_dispatcher import WorkflowDispatcher
from workflow.workflow_engine import WorkflowEngine, WorkflowExecutionSummary
from workflow.workflow_executor import WorkflowExecutor
from workflow.workflow_history import WorkflowHistory
from workflow.workflow_logger import WorkflowLogger
from workflow.workflow_metrics import WorkflowMetrics
from workflow.workflow_registry import WorkflowRecord, WorkflowRegistry
from workflow.workflow_recovery import WorkflowRecovery
from workflow.workflow_scheduler import WorkflowScheduler
from workflow.workflow_state import WorkflowState, WorkflowStatus
from workflow.workflow_validator import WorkflowValidator


@dataclass(frozen=True, slots=True)
class WorkflowStatistics:
    workflow_engine_status: str
    workflow_registry_status: str
    workflow_scheduler_status: str
    workflow_recovery_status: str
    registered_workflow_templates: int
    active_workflows: int
    overall_workflow_health: str


class WorkflowManager:
    initialized = True

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger("workflow")
        self.engine = WorkflowEngine()
        self.registry = self.engine.registry
        self.builder = self.engine.builder
        self.executor = self.engine.executor
        self.dispatcher = self.engine.dispatcher
        self.scheduler = self.engine.scheduler
        self.validator = self.engine.validator
        self.history = WorkflowHistory()
        self.metrics = WorkflowMetrics()
        self.logger_factory = WorkflowLogger(self.logger)
        self.recovery = WorkflowRecovery()
        self.checkpoint = WorkflowCheckpoint("bootstrap", "bootstrap", "ready")
        self.diagnostics = WorkflowDiagnostics()
        self._active = 0

    def initialize(self) -> WorkflowStatistics:
        self.logger.info("workflow_engine_initialized")
        return self.statistics()

    def create_workflow(self, definition: WorkflowDefinition, category: str = "general") -> WorkflowRecord:
        self.metrics.created += 1
        self._active += 1
        self.logger.info("workflow_created workflow_id=%s", definition.workflow_id)
        return self.engine.create_workflow(definition, category=category)

    def statistics(self) -> WorkflowStatistics:
        registry_stats = self.registry.statistics()
        return WorkflowStatistics(
            workflow_engine_status="ready" if self.engine.initialized else "unavailable",
            workflow_registry_status="ready" if self.registry.initialized else "unavailable",
            workflow_scheduler_status="ready" if self.scheduler.initialized else "unavailable",
            workflow_recovery_status="ready" if self.recovery.initialized else "unavailable",
            registered_workflow_templates=registry_stats["registered_workflows"],
            active_workflows=self._active,
            overall_workflow_health="healthy",
        )
