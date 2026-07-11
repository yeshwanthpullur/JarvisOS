"""Task intelligence manager for projects, goals, milestones, and scheduling."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from task_intelligence.dependency_manager import DependencyManager
from task_intelligence.goal_manager import GoalManager
from task_intelligence.milestone_manager import MilestoneManager
from task_intelligence.priority_engine import PriorityEngine
from task_intelligence.progress_tracker import ProgressTracker
from task_intelligence.project_manager import ProjectManager
from task_intelligence.schedule_engine import ScheduleEngine
from task_intelligence.task_dashboard import TaskDashboard
from task_intelligence.task_diagnostics import TaskDiagnostics
from task_intelligence.task_history import TaskHistory
from task_intelligence.task_metrics import TaskMetrics
from task_intelligence.task_templates import TaskTemplates
from task_intelligence.task_validator import TaskValidator


@dataclass(frozen=True, slots=True)
class TaskIntelligenceStatistics:
    """Summary statistics for task intelligence."""

    projects: int
    goals: int
    milestones: int
    status: str


class TaskIntelligenceManager:
    """Central orchestration layer for task intelligence."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.project_manager = ProjectManager(logger=self._logger)
        self.goal_manager = GoalManager(logger=self._logger)
        self.milestone_manager = MilestoneManager(logger=self._logger)
        self.priority_engine = PriorityEngine(logger=self._logger)
        self.schedule_engine = ScheduleEngine(logger=self._logger)
        self.dependency_manager = DependencyManager(logger=self._logger)
        self.progress_tracker = ProgressTracker(logger=self._logger)
        self.dashboard = TaskDashboard(logger=self._logger)
        self.templates = TaskTemplates(logger=self._logger)
        self.metrics = TaskMetrics(logger=self._logger)
        self.validator = TaskValidator(logger=self._logger)
        self.diagnostics = TaskDiagnostics(logger=self._logger)
        self.history = TaskHistory(logger=self._logger)
        self.initialized = False

    def initialize(self) -> TaskIntelligenceStatistics:
        self.project_manager.initialize()
        self.goal_manager.initialize()
        self.milestone_manager.initialize()
        self.priority_engine.initialize()
        self.schedule_engine.initialize()
        self.dependency_manager.initialize()
        self.progress_tracker.initialize()
        self.dashboard.initialize()
        self.templates.initialize()
        self.metrics.initialize()
        self.validator.initialize()
        self.diagnostics.initialize()
        self.history.initialize()
        self.initialized = True
        self._logger.info("task_intelligence_initialized")
        return self.statistics()

    def statistics(self) -> TaskIntelligenceStatistics:
        self._ensure_initialized()
        return TaskIntelligenceStatistics(
            projects=len(self.project_manager.list_projects()),
            goals=len(self.goal_manager.list_goals()),
            milestones=len(self.milestone_manager.list_milestones()),
            status="ready",
        )

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("TaskIntelligenceManager must be initialized before use.")
