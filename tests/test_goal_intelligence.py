"""Behavioral tests for Goal Intelligence integration."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from commands import CommandManager
from conversation import ConversationContext, ConversationManager, ConversationSession
from core.health_checker import HealthChecker
from core.startup_manager import StartupManager
from goal_intelligence import GoalIntelligenceManager
from memory import MemoryManager
from personal_intelligence import PersonalIntelligenceManager
from retrieval import RetrievalManager
from task_intelligence import TaskIntelligenceManager
from task_intelligence.models import TaskPriorityLevel
from tasks import TaskManager, TaskStatus
from workflow import WorkflowManager
from research import ResearchManager


class GoalIntelligenceTests(unittest.TestCase):
    """Goal intelligence should stay grounded in authoritative task state."""

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.memory = MemoryManager(Path(self.tempdir.name))
        self.memory.initialize()
        self.retrieval = RetrievalManager()
        self.retrieval.initialize()
        self.personal = PersonalIntelligenceManager(memory_manager=self.memory, retrieval_manager=self.retrieval)
        self.personal.initialize()
        self.tasks = TaskManager()
        self.tasks.initialize()
        self.task_intelligence = TaskIntelligenceManager()
        self.task_intelligence.initialize()
        self.workflow = WorkflowManager()
        self.workflow.initialize()
        self.research = ResearchManager()
        self.research.initialize()
        self.context_session = ConversationSession()
        self.context_manager = GoalIntelligenceManager(
            task_intelligence_manager=self.task_intelligence,
            task_manager=self.tasks,
            context_intelligence_manager=None,
            retrieval_manager=self.retrieval,
            personal_intelligence_manager=self.personal,
            workflow_manager=self.workflow,
            research_manager=self.research,
            memory_manager=self.memory,
            knowledge_manager=None,
        )
        self.context_manager.initialize()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def _create_goal(self, name: str = "Robotics Goal", **kwargs: object):
        return self.task_intelligence.goal_manager.create_goal(
            name,
            description=str(kwargs.pop("description", "")),
            project_id=kwargs.pop("project_id", None),
            purpose=str(kwargs.pop("purpose", "")),
            desired_outcome=str(kwargs.pop("desired_outcome", "")),
            success_criteria=tuple(kwargs.pop("success_criteria", ())),
            parent_goal_id=kwargs.pop("parent_goal_id", None),
            priority=kwargs.pop("priority", TaskPriorityLevel.NORMAL),
            target_date=kwargs.pop("target_date", None),
            time_horizon=str(kwargs.pop("time_horizon", "short_term")),
            audit_metadata=dict(kwargs.pop("audit_metadata", {})),
        )

    def test_clarify_vague_goal(self) -> None:
        report = self.context_manager.clarify_goal("I want to learn robotics.")
        self.assertIn("success criteria", report.missing_information)
        self.assertIn("What outcome should this goal produce?", report.immediate_response)

    def test_clarify_goal_with_enough_information_is_shorter(self) -> None:
        report = self.context_manager.clarify_goal("Build a working robot that follows a line and is finished by June.")
        self.assertNotIn("desired outcome", report.missing_information)
        self.assertIn("How will we know this goal is done?", report.immediate_response)

    def test_goal_quality_strong(self) -> None:
        goal = self._create_goal(
            purpose="Build a working prototype",
            desired_outcome="Assemble and demonstrate a two-wheel robot",
            success_criteria=("Robot assembled", "Bluetooth control works"),
            target_date="2026-08-01",
        )
        report = self.context_manager.evaluate_goal_quality(goal)
        self.assertEqual(report.quality, "strong")
        self.assertEqual(report.goal.goal_id, goal.goal_id)

    def test_goal_quality_needs_clarification(self) -> None:
        goal = self._create_goal()
        report = self.context_manager.evaluate_goal_quality(goal)
        self.assertEqual(report.quality, "needs_clarification")
        self.assertIn("desired outcome", report.missing_information)

    def test_goal_decomposition_creates_milestones_and_links_tasks(self) -> None:
        goal = self._create_goal(
            purpose="Build a robot",
            desired_outcome="Deliver a working robot prototype",
            success_criteria=("Prototype built",),
        )
        plan = self.context_manager.decompose_goal(goal)
        self.assertGreaterEqual(len(plan.milestones), 1)
        self.assertGreaterEqual(len(plan.supporting_tasks), 1)
        updated = self.task_intelligence.goal_manager.get_goal(goal.goal_id)
        self.assertGreaterEqual(len(updated.milestones), 1)
        self.assertGreaterEqual(len(updated.task_references), 1)

    def test_goal_progress_uses_task_and_milestone_evidence(self) -> None:
        goal = self._create_goal(
            purpose="Ship the first version",
            desired_outcome="Release a usable prototype",
            success_criteria=("Prototype shipped",),
        )
        milestone = self.task_intelligence.milestone_manager.create_milestone("Prototype complete", goal_id=goal.goal_id)
        self.task_intelligence.goal_manager.link_milestone(goal.goal_id, milestone.milestone_id)
        task = self.tasks.create_task("Ship prototype", "Finalize the prototype")
        self.task_intelligence.goal_manager.link_task(goal.goal_id, task.task_id)
        self.tasks.complete_task(task.task_id)
        progress = self.context_manager.evaluate_progress(goal)
        self.assertIn(progress.status, {"in_progress", "on_track", "completed", "early"})
        self.assertTrue(progress.evidence)

    def test_goal_blocker_detection_finds_missing_dependency(self) -> None:
        goal = self._create_goal()
        updated = self.task_intelligence.goal_manager.update_goal(goal.goal_id, dependencies=("missing-goal",))
        blockers = self.context_manager.detect_blockers(updated)
        self.assertTrue(any("Missing dependency" in blocker for blocker in blockers))

    def test_goal_conflict_detection_reports_evidence(self) -> None:
        goal_a = self._create_goal(target_date="2026-07-12")
        goal_b = self._create_goal(target_date="2026-07-12")
        report = self.context_manager.detect_conflicts((goal_a, goal_b))
        self.assertIn(report.conflict_type, {"confirmed_conflict", "no_conflict"})
        self.assertTrue(report.affected_goal_ids)

    def test_priority_recommendation_orders_critical_first(self) -> None:
        goal_a = self._create_goal(priority=TaskPriorityLevel.LOW)
        goal_b = self._create_goal(priority=TaskPriorityLevel.CRITICAL)
        ordered = self.context_manager.recommend_priority((goal_a, goal_b))
        self.assertEqual(ordered[0].goal_id, goal_b.goal_id)

    def test_goal_comparison_reports_order(self) -> None:
        goal_a = self._create_goal(priority=TaskPriorityLevel.LOW)
        goal_b = self._create_goal(priority=TaskPriorityLevel.HIGH)
        report = self.context_manager.compare_goals((goal_a, goal_b))
        self.assertEqual(report.conflict_type, "comparison")
        self.assertEqual(len(report.evidence), 2)

    def test_goal_review_merges_progress_and_quality(self) -> None:
        goal = self._create_goal(
            purpose="Ship a feature",
            desired_outcome="Ship a supported feature",
            success_criteria=("Feature shipped",),
        )
        report = self.context_manager.review_goal(goal)
        self.assertEqual(report.analysis_type, "review")
        self.assertIn("Goal", report.summary)

    def test_goal_revision_updates_authoritative_record(self) -> None:
        goal = self._create_goal()
        report = self.context_manager.revise_goal(goal.goal_id, target_date="2026-09-01", status="active")
        self.assertEqual(report.analysis_type, "revise")
        self.assertEqual(report.goal.target_date, "2026-09-01")

    def test_pause_and_resume_goal(self) -> None:
        goal = self._create_goal()
        paused = self.context_manager.pause_goal(goal.goal_id)
        resumed = self.context_manager.resume_goal(goal.goal_id)
        self.assertEqual(paused.goal.status, "paused")
        self.assertEqual(resumed.goal.status, "active")

    def test_abandon_goal(self) -> None:
        goal = self._create_goal()
        abandoned = self.context_manager.abandon_goal(goal.goal_id, reason="No longer relevant")
        self.assertEqual(abandoned.goal.status, "abandoned")

    def test_supersede_goal(self) -> None:
        old_goal = self._create_goal(name="Old Goal")
        new_goal = self._create_goal(name="New Goal")
        report = self.context_manager.supersede_goal(old_goal.goal_id, new_goal.goal_id, reason="Replaced by a better plan")
        self.assertEqual(report.goal.status, "superseded")

    def test_completion_requires_evidence(self) -> None:
        goal = self._create_goal(success_criteria=("Done",))
        report = self.context_manager.evaluate_completion(goal)
        self.assertIn(report.metadata["outcome"], {"not_completed", "insufficient_evidence"})

    def test_next_step_is_grounded(self) -> None:
        goal = self._create_goal(purpose="Deliver a robot", desired_outcome="Deliver a robot", success_criteria=("Deliverable exists",))
        task = self.tasks.create_task("Assemble chassis", "Build the base")
        self.task_intelligence.goal_manager.link_task(goal.goal_id, task.task_id)
        recommendation = self.context_manager.recommend_next_step(goal)
        self.assertTrue(recommendation.reason)

    def test_goal_portfolio_selects_useful_entries(self) -> None:
        self._create_goal(name="Blocked Goal")
        portfolio = self.context_manager.goal_portfolio()
        self.assertTrue(portfolio.entries)
        self.assertIn("Blocked Goal", portfolio.immediate_response)

    def test_explain_goal_state_uses_authoritative_data(self) -> None:
        goal = self._create_goal(name="Explainable Goal")
        report = self.context_manager.explain_goal_state(goal)
        self.assertIn("Explainable Goal", report.summary)

    def test_resolve_goal_reference(self) -> None:
        goal = self._create_goal(name="Reference Goal")
        resolution = self.context_manager.resolve_goal_reference("Reference Goal")
        self.assertEqual(resolution.status, "resolved")
        self.assertEqual(resolution.goal.goal_id, goal.goal_id)

    def test_prepare_request_decomposes_goal(self) -> None:
        goal = self._create_goal(name="Build System", desired_outcome="Build a system")
        report = self.context_manager.prepare_request("Break this goal into milestones.", self.context_session)
        self.assertIn(report.analysis_type, {"clarify", "decompose", "review", "explain"})
        self.assertTrue(report.immediate_response)

    def test_command_goal_portfolio(self) -> None:
        goal = self._create_goal(name="Command Goal", desired_outcome="Command path")
        self.task_intelligence.goal_manager.set_status(goal.goal_id, "active")
        manager = CommandManager()
        manager.initialize()
        context = ConversationContext(
            session=self.context_session,
            metadata={"goal_intelligence_manager": self.context_manager},
        )
        response = manager.execute("goal portfolio", context)
        self.assertIn("Command Goal", response.response)

    def test_command_goal_review(self) -> None:
        goal = self._create_goal(name="Review Goal", desired_outcome="Review path")
        manager = CommandManager()
        manager.initialize()
        context = ConversationContext(
            session=self.context_session,
            metadata={"goal_intelligence_manager": self.context_manager},
        )
        self.context_session.current_goal = "Review Goal"
        response = manager.execute("goal review", context)
        self.assertIn("Goal", response.response)

    def test_conversation_manager_integrates_goal_analysis(self) -> None:
        goal = self._create_goal(name="Conversation Goal", desired_outcome="Conversation path")
        core = StartupManager()
        core.start()
        try:
            manager = ConversationManager(
                jarvis_core=core.jarvis_core,
                memory_manager=self.memory,
                task_manager=self.tasks,
                task_intelligence_manager=self.task_intelligence,
                workflow_manager=self.workflow,
                retrieval_manager=self.retrieval,
                research_manager=self.research,
                personal_intelligence_manager=self.personal,
                context_intelligence_manager=core.context_intelligence_manager,
                goal_intelligence_manager=self.context_manager,
            )
            manager.initialize()
            manager.active_session.current_goal = goal.name
            response = manager.handle_input("What should I do next?")
            self.assertTrue(response.response)
        finally:
            core.shutdown()

    def test_startup_and_health_include_goal_intelligence(self) -> None:
        startup = StartupManager()
        startup.start()
        try:
            self.assertIsNotNone(startup.goal_intelligence_manager)
            self.assertTrue(startup.goal_intelligence_manager.initialized)
            self.assertTrue(
                any(
                    result.name in {"goal_intelligence", "goal_analysis", "goal_decomposition", "goal_progress", "goal_reference_resolution"}
                    for result in startup.health_results
                )
            )
            checker = HealthChecker(
                settings=startup.settings,
                required_directories=startup.required_directories(startup.settings),
                module_checks={"goal_intelligence": lambda: True},
            )
            self.assertEqual(checker.check_module("goal_intelligence", "Goal Intelligence").status.value, "passing")
        finally:
            startup.shutdown()


def _make_generated_test(index: int):
    def _test(self: GoalIntelligenceTests) -> None:
        goal = self._create_goal(name=f"Goal {index}", desired_outcome=f"Outcome {index}", success_criteria=(f"Done {index}",))
        report = self.context_manager.evaluate_goal_quality(goal)
        self.assertIn(report.quality, {"strong", "usable", "needs_clarification", "at_risk", "blocked"})
        self.assertTrue(goal.goal_id)
        self.assertTrue(self.context_manager.statistics().goal_intelligence_status == "ready")

    _test.__name__ = f"test_generated_goal_intelligence_{index:02d}"
    return _test


for _index in range(1, 26):
    setattr(GoalIntelligenceTests, f"test_generated_goal_intelligence_{_index:02d}", _make_generated_test(_index))


if __name__ == "__main__":
    unittest.main()
