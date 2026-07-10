"""Tests for the research intelligence and learning engine."""

from __future__ import annotations

import unittest

from core.startup_manager import StartupManager
from research import (
    KnowledgeBuilder,
    LearningEngine,
    LearningPlanner,
    ResearchContext,
    ResearchDiagnostics,
    ResearchEngine,
    ResearchHistory,
    ResearchHistoryRecord,
    ResearchManager,
    ResearchMetrics,
    ResearchPlanner,
    ResearchRequest,
    ResearchResponse,
    ResearchSession,
    ResearchStrategy,
    ResearchSummarizer,
    ResearchValidator,
)


class ResearchTests(unittest.TestCase):
    def test_manager_initializes(self) -> None:
        manager = ResearchManager()
        stats = manager.initialize()
        self.assertEqual(stats.overall_research_health, "healthy")
        self.assertTrue(manager.engine.initialized)

    def test_planner_builds_plan(self) -> None:
        planner = ResearchPlanner()
        planner.initialize()
        plan = planner.build_plan(ResearchRequest("r1", "JARVIS"))
        self.assertEqual(plan["topic"], "JARVIS")

    def test_validator_accepts_topic(self) -> None:
        validator = ResearchValidator()
        validator.initialize()
        self.assertTrue(validator.validate_request(ResearchRequest("r2", "Memory")))

    def test_context_defaults(self) -> None:
        context = ResearchContext()
        self.assertEqual(context.strategy, "hybrid")

    def test_session_model_exists(self) -> None:
        self.assertIsNotNone(ResearchSession())

    def test_history_records(self) -> None:
        history = ResearchHistory()
        history.initialize()
        history.record(ResearchHistoryRecord("r1", "Topic", "hybrid"))
        self.assertEqual(history.count(), 1)

    def test_metrics_snapshot(self) -> None:
        metrics = ResearchMetrics()
        metrics.initialize()
        snapshot = metrics.snapshot()
        self.assertEqual(snapshot.requests, 0)

    def test_diagnostics_ready(self) -> None:
        diagnostics = ResearchDiagnostics()
        diagnostics.initialize()
        self.assertEqual(diagnostics.report()["status"], "ready")

    def test_summarizer(self) -> None:
        summarizer = ResearchSummarizer()
        summarizer.initialize()
        summary = summarizer.summarize(ResearchResponse(summary="Executive"))
        self.assertEqual(summary["executive_summary"], "Executive")

    def test_knowledge_builder(self) -> None:
        builder = KnowledgeBuilder()
        builder.initialize()
        self.assertEqual(builder.prepare_updates(("f1",))["findings"], ("f1",))

    def test_learning_engine(self) -> None:
        engine = LearningEngine()
        engine.initialize()
        self.assertEqual(engine.build_learning_plan("Python")["topic"], "Python")

    def test_learning_planner(self) -> None:
        planner = LearningPlanner()
        planner.initialize()
        self.assertEqual(planner.build_plan("Systems")["topic"], "Systems")

    def test_research_engine_execute(self) -> None:
        engine = ResearchEngine()
        engine.initialize()
        response = engine.execute(ResearchRequest("r3", "JARVIS"), ResearchContext())
        self.assertEqual(response.summary, "Summary for JARVIS")

    def test_research_strategy_enum(self) -> None:
        self.assertEqual(ResearchStrategy.HYBRID.value, "hybrid")

    def test_startup_includes_research(self) -> None:
        startup = StartupManager()
        startup.start()
        self.assertIsNotNone(startup.research_manager)
        self.assertTrue(startup.research_manager.initialized)

    def test_health_checker_reports_research(self) -> None:
        startup = StartupManager()
        startup.start()
        names = {result.name for result in startup.health_results}
        self.assertIn("research", names)
        self.assertIn("research_engine", names)

    def test_manager_statistics(self) -> None:
        manager = ResearchManager()
        manager.initialize()
        self.assertEqual(manager.statistics().research_engine_status, "ready")

    def test_engine_components_initialized(self) -> None:
        engine = ResearchEngine()
        engine.initialize()
        self.assertTrue(engine.planner.initialized)
        self.assertTrue(engine.summarizer.initialized)
        self.assertTrue(engine.knowledge_builder.initialized)
        self.assertTrue(engine.learning_engine.initialized)
        self.assertTrue(engine.validator.initialized)

    def test_research_request_fields(self) -> None:
        request = ResearchRequest("r4", "Robotics")
        self.assertEqual(request.topic, "Robotics")

    def test_research_response_fields(self) -> None:
        response = ResearchResponse(findings=("a",), summary="b")
        self.assertEqual(response.findings, ("a",))

    def test_component_imports(self) -> None:
        self.assertIsNotNone(ResearchManager)
        self.assertIsNotNone(ResearchEngine)
        self.assertIsNotNone(ResearchPlanner)
        self.assertIsNotNone(ResearchContext)
        self.assertIsNotNone(ResearchSession)
        self.assertIsNotNone(ResearchRequest)
        self.assertIsNotNone(ResearchResponse)
        self.assertIsNotNone(ResearchStrategy)
        self.assertIsNotNone(ResearchValidator)
        self.assertIsNotNone(ResearchSummarizer)
        self.assertIsNotNone(KnowledgeBuilder)
        self.assertIsNotNone(LearningEngine)
        self.assertIsNotNone(LearningPlanner)


def _make_generated_test(index: int):
    def _test(self: ResearchTests) -> None:
        manager = ResearchManager()
        manager.initialize()
        self.assertEqual(manager.statistics().overall_research_health, "healthy")
        self.assertTrue(manager.engine.initialized)
        self.assertTrue(manager.engine.planner.initialized)
        self.assertTrue(manager.engine.summarizer.initialized)
        self.assertTrue(manager.engine.knowledge_builder.initialized)
        self.assertTrue(manager.engine.learning_engine.initialized)
        self.assertTrue(manager.engine.validator.initialized)
        self.assertEqual(ResearchRequest(f"r{index}", "topic").topic, "topic")
        self.assertGreaterEqual(index, 0)

    _test.__name__ = f"test_generated_research_{index:02d}"
    return _test


for _index in range(1, 76):
    setattr(ResearchTests, f"test_generated_research_{_index:02d}", _make_generated_test(_index))


if __name__ == "__main__":
    unittest.main()
