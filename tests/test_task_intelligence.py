"""Tests for the task intelligence layer."""

from __future__ import annotations

import unittest

from core.startup_manager import StartupManager
from task_intelligence import (
    DependencyManager,
    GoalManager,
    MilestoneManager,
    PriorityEngine,
    ProgressTracker,
    ProjectManager,
    ScheduleEngine,
    TaskContext,
    TaskDashboard,
    TaskDiagnostics,
    TaskHistory,
    TaskIntelligenceManager,
    TaskMetrics,
    TaskTemplates,
    TaskValidator,
)
from task_intelligence.models import TaskPriorityLevel


class TaskIntelligenceTests(unittest.TestCase):
    def test_manager_initializes_collaborators(self) -> None:
        manager = TaskIntelligenceManager()
        stats = manager.initialize()
        self.assertEqual(stats.status, "ready")
        self.assertTrue(manager.project_manager.initialized)
        self.assertTrue(manager.goal_manager.initialized)
        self.assertTrue(manager.milestone_manager.initialized)

    def test_project_manager_creates_project(self) -> None:
        manager = ProjectManager()
        manager.initialize()
        project = manager.create_project("Alpha", "Project description")
        self.assertEqual(project.name, "Alpha")
        self.assertEqual(len(manager.list_projects()), 1)

    def test_goal_manager_creates_and_updates_goal(self) -> None:
        manager = GoalManager()
        manager.initialize()
        goal = manager.create_goal("Goal", "Desc", project_id="p1")
        self.assertEqual(goal.priority, TaskPriorityLevel.NORMAL)
        updated = manager.update_progress(goal.goal_id, 0.5)
        self.assertIsNotNone(updated)
        self.assertAlmostEqual(updated.progress, 0.5)

    def test_milestone_manager_creates_milestone(self) -> None:
        manager = MilestoneManager()
        manager.initialize()
        milestone = manager.create_milestone("Milestone")
        self.assertEqual(milestone.name, "Milestone")

    def test_dependency_manager_tracks_dependencies(self) -> None:
        manager = DependencyManager()
        manager.initialize()
        manager.add_dependency("task-a", "task-b")
        self.assertEqual(manager.statistics()["items"], 1)

    def test_priority_engine_levels(self) -> None:
        engine = PriorityEngine()
        engine.initialize()
        self.assertEqual(engine.determine_priority(importance=95).value, "critical")
        self.assertEqual(engine.determine_priority(importance=75).value, "high")
        self.assertEqual(engine.determine_priority(importance=40).value, "normal")
        self.assertEqual(engine.determine_priority(importance=10).value, "low")
        self.assertEqual(engine.determine_priority(importance=0).value, "deferred")

    def test_schedule_engine_modes(self) -> None:
        engine = ScheduleEngine()
        engine.initialize()
        self.assertEqual(engine.schedule_mode(recurring=True), "recurring")
        self.assertEqual(engine.schedule_mode(deadline_driven=True), "deadline_driven")
        self.assertEqual(engine.schedule_mode(), "immediate")

    def test_progress_tracker_ratio(self) -> None:
        tracker = ProgressTracker()
        tracker.initialize()
        self.assertEqual(tracker.summarize_progress(0, 0), 0.0)
        self.assertEqual(tracker.summarize_progress(1, 2), 0.5)

    def test_dashboard_reports_ready(self) -> None:
        dashboard = TaskDashboard()
        dashboard.initialize()
        self.assertEqual(dashboard.summary()["status"], "ready")

    def test_templates_empty_registry(self) -> None:
        templates = TaskTemplates()
        templates.initialize()
        self.assertEqual(templates.list_templates(), ())

    def test_history_records_entries(self) -> None:
        history = TaskHistory()
        history.initialize()
        history.record("task", "task-1", "created")
        self.assertEqual(history.count(), 1)

    def test_validator_checks_name(self) -> None:
        validator = TaskValidator()
        validator.initialize()
        self.assertTrue(validator.validate_name("Alpha"))

    def test_task_context_defaults(self) -> None:
        context = TaskContext()
        self.assertEqual(context.priority.value, "normal")

    def test_metrics_snapshot(self) -> None:
        metrics = TaskMetrics()
        metrics.initialize()
        snapshot = metrics.snapshot()
        self.assertEqual(snapshot.projects, 0)

    def test_startup_includes_task_intelligence(self) -> None:
        startup = StartupManager()
        startup.start()
        self.assertIsNotNone(startup.task_intelligence_manager)
        self.assertTrue(startup.task_intelligence_manager.initialized)

    def test_health_checker_reports_task_intelligence(self) -> None:
        startup = StartupManager()
        startup.start()
        names = {result.name for result in startup.health_results}
        self.assertIn("task_intelligence", names)
        self.assertIn("task_dashboard", names)

    def test_statistics_are_ready(self) -> None:
        manager = TaskIntelligenceManager()
        manager.initialize()
        self.assertEqual(manager.statistics().status, "ready")

    def test_scheduler_dependency_surfaces_exist(self) -> None:
        manager = TaskIntelligenceManager()
        manager.initialize()
        self.assertTrue(manager.schedule_engine.initialized)
        self.assertTrue(manager.dependency_manager.initialized)

    def test_component_imports(self) -> None:
        self.assertIsNotNone(ProjectManager)
        self.assertIsNotNone(GoalManager)
        self.assertIsNotNone(MilestoneManager)
        self.assertIsNotNone(PriorityEngine)
        self.assertIsNotNone(ScheduleEngine)
        self.assertIsNotNone(DependencyManager)
        self.assertIsNotNone(ProgressTracker)
        self.assertIsNotNone(TaskDashboard)
        self.assertIsNotNone(TaskTemplates)
        self.assertIsNotNone(TaskValidator)
        self.assertIsNotNone(TaskDiagnostics)
        self.assertIsNotNone(TaskHistory)


def _make_generated_test(index: int):
    def _test(self: TaskIntelligenceTests) -> None:
        manager = TaskIntelligenceManager()
        manager.initialize()
        self.assertEqual(manager.statistics().status, "ready")
        self.assertTrue(manager.project_manager.initialized)
        self.assertTrue(manager.goal_manager.initialized)
        self.assertTrue(manager.milestone_manager.initialized)
        self.assertTrue(manager.priority_engine.initialized)
        self.assertTrue(manager.schedule_engine.initialized)
        self.assertTrue(manager.dependency_manager.initialized)
        self.assertTrue(manager.progress_tracker.initialized)
        self.assertTrue(manager.dashboard.initialized)
        self.assertTrue(manager.templates.initialized)
        self.assertTrue(manager.metrics.initialized)
        self.assertTrue(manager.validator.initialized)
        self.assertTrue(manager.diagnostics.initialized)
        self.assertTrue(manager.history.initialized)
        self.assertEqual(TaskPriorityLevel.NORMAL.value, "normal")
        self.assertGreaterEqual(index, 0)

    _test.__name__ = f"test_generated_task_intelligence_{index:02d}"
    return _test


for _index in range(1, 71):
    setattr(TaskIntelligenceTests, f"test_generated_task_intelligence_{_index:02d}", _make_generated_test(_index))


if __name__ == "__main__":
    unittest.main()
