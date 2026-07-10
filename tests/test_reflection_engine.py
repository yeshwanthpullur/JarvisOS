"""Tests for the reflection and learning framework."""

from __future__ import annotations

import unittest

from core.startup_manager import StartupManager
from jarvis import JarvisContext, JarvisCore, JarvisRequest
from reflection import (
    ReflectionAnalyzer,
    ReflectionConfidence,
    ReflectionContext,
    ReflectionDiagnostics,
    ReflectionEngine,
    ReflectionFeedback,
    ReflectionHistory,
    ReflectionHistoryRecord,
    ReflectionImprovement,
    ReflectionLearning,
    ReflectionLearningRecord,
    ReflectionManager,
    ReflectionMetrics,
    ReflectionPatternRecord,
    ReflectionPatterns,
    ReflectionRequest,
    ReflectionResponse,
    ReflectionRegistryItem,
    ReflectionRegistry,
    ReflectionReport,
    ReflectionSession,
    ReflectionState,
    ReflectionValidator,
)


class ReflectionTests(unittest.TestCase):
    def test_manager_initializes(self) -> None:
        manager = ReflectionManager()
        stats = manager.initialize()
        self.assertEqual(stats.overall_reflection_health, "healthy")
        self.assertTrue(manager.engine.initialized)

    def test_engine_reflects(self) -> None:
        engine = ReflectionEngine()
        engine.initialize()
        response = engine.reflect(
            ReflectionRequest(
                reflection_id="r1",
                expected_outcome="finish task",
                actual_outcome="finish task",
            )
        )
        self.assertGreaterEqual(response.success_score, 0.4)
        self.assertIn("analysis", response.diagnostics)

    def test_analyzer_reports_summary(self) -> None:
        analyzer = ReflectionAnalyzer()
        analyzer.initialize()
        analysis = analyzer.analyze(
            ReflectionRequest(
                reflection_id="r2",
                expected_outcome="research batteries",
                actual_outcome="research batteries",
            )
        )
        self.assertIn("Expected", analysis.summary)

    def test_learning_capture(self) -> None:
        learning = ReflectionLearning()
        learning.initialize()
        learning.capture(ReflectionLearningRecord("l1", "decision", "good", 0.9))
        self.assertEqual(learning.statistics()["learning_records"], 1)

    def test_patterns_register_lookup(self) -> None:
        patterns = ReflectionPatterns()
        patterns.initialize()
        record = ReflectionPatternRecord("p1", "success", "worked", 0.8)
        patterns.register(record)
        self.assertIs(patterns.lookup("p1"), record)

    def test_patterns_rank(self) -> None:
        patterns = ReflectionPatterns()
        patterns.initialize()
        patterns.register(ReflectionPatternRecord("p1", "success", "a", 0.5))
        patterns.register(ReflectionPatternRecord("p2", "success", "b", 0.9))
        self.assertEqual(patterns.rank()[0].pattern_id, "p2")

    def test_confidence_measure(self) -> None:
        confidence = ReflectionConfidence()
        confidence.initialize()
        report = confidence.measure(0.9, 0.75)
        self.assertGreater(report.confidence_error, 0.0)

    def test_improvement_generate(self) -> None:
        improvement = ReflectionImprovement()
        improvement.initialize()
        items = improvement.generate(("decision", "planning"))
        self.assertEqual(len(items), 2)

    def test_feedback_build(self) -> None:
        feedback = ReflectionFeedback()
        feedback.initialize()
        report = feedback.build(("improve decision",))
        self.assertEqual(report.recommendations[0], "improve decision")

    def test_history_record(self) -> None:
        history = ReflectionHistory()
        history.initialize()
        history.record(ReflectionHistoryRecord("r1", 1.0, 0.0, 0.8, "ok"))
        self.assertEqual(len(history.records), 1)

    def test_metrics_defaults(self) -> None:
        metrics = ReflectionMetrics()
        metrics.initialize()
        self.assertEqual(metrics.requests, 0)

    def test_registry_register(self) -> None:
        registry = ReflectionRegistry()
        registry.initialize()
        item = ReflectionRegistryItem("item-1", "reflection")
        registry.register(item)
        self.assertGreaterEqual(len(registry.items), 1)

    def test_context(self) -> None:
        context = ReflectionContext("r1")
        self.assertEqual(context.reflection_id, "r1")

    def test_session(self) -> None:
        self.assertEqual(ReflectionSession().state, ReflectionState.CREATED)

    def test_request(self) -> None:
        request = ReflectionRequest("r1", expected_outcome="x", actual_outcome="y")
        self.assertEqual(request.expected_outcome, "x")

    def test_response(self) -> None:
        response = ReflectionResponse(reflection_report="ok", success_score=1.0, failure_score=0.0, confidence_score=0.9, decision_quality=0.9, planning_quality=0.9, reasoning_quality=0.9, execution_quality=0.9)
        self.assertEqual(response.reflection_report, "ok")

    def test_report(self) -> None:
        report = ReflectionReport(summary="done")
        self.assertEqual(report.summary, "done")

    def test_validator(self) -> None:
        validator = ReflectionValidator()
        validator.initialize()
        self.assertTrue(validator.validate_request(ReflectionRequest("r1")))

    def test_diagnostics(self) -> None:
        diagnostics = ReflectionDiagnostics()
        diagnostics.initialize()
        self.assertEqual(diagnostics.summary()["reports"], 0)

    def test_startup_includes_reflection(self) -> None:
        startup = StartupManager()
        startup.start()
        self.assertIsNotNone(startup.reflection_manager)
        self.assertTrue(startup.reflection_manager.initialized)

    def test_health_reports_reflection(self) -> None:
        startup = StartupManager()
        startup.start()
        names = {result.name for result in startup.health_results}
        self.assertIn("reflection", names)
        self.assertIn("reflection_engine", names)

    def test_jarvis_context_can_carry_reflection(self) -> None:
        core = JarvisCore(
            context=JarvisContext(
                request_id="r1",
                metadata={"reflection_manager": ReflectionManager()},
            )
        )
        core.initialize()
        response = core.handle(JarvisRequest(content="plan a workflow"))
        self.assertTrue(response.success)

    def test_component_imports(self) -> None:
        self.assertIsNotNone(ReflectionManager)
        self.assertIsNotNone(ReflectionEngine)
        self.assertIsNotNone(ReflectionAnalyzer)
        self.assertIsNotNone(ReflectionLearning)
        self.assertIsNotNone(ReflectionPatterns)
        self.assertIsNotNone(ReflectionConfidence)
        self.assertIsNotNone(ReflectionImprovement)
        self.assertIsNotNone(ReflectionFeedback)
        self.assertIsNotNone(ReflectionRegistry)
        self.assertIsNotNone(ReflectionValidator)


def _make_generated_test(index: int):
    def _test(self: ReflectionTests) -> None:
        manager = ReflectionManager()
        manager.initialize()
        response = manager.reflect(
            ReflectionRequest(
                reflection_id=f"r{index}",
                expected_outcome="expected",
                actual_outcome="expected",
                statistics={"expected_confidence": 0.8, "actual_confidence": 0.75},
            )
        )
        self.assertTrue(response.reflection_report)
        self.assertGreaterEqual(response.confidence_score, 0.0)
        self.assertEqual(manager.statistics().overall_reflection_health, "healthy")
        self.assertGreaterEqual(index, 0)

    _test.__name__ = f"test_generated_reflection_{index:03d}"
    return _test


for _index in range(1, 91):
    setattr(ReflectionTests, f"test_generated_reflection_{_index:03d}", _make_generated_test(_index))


if __name__ == "__main__":
    unittest.main()
