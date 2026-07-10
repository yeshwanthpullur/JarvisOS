"""Tests for the adaptive intelligence loop."""

from __future__ import annotations

import unittest

from adaptive import (
    AdaptiveContext,
    AdaptiveDiagnostics,
    AdaptiveEngine,
    AdaptiveExperience,
    AdaptiveExperienceRecord,
    AdaptiveFeedback,
    AdaptiveHistory,
    AdaptiveHistoryRecord,
    AdaptiveLearningQueue,
    AdaptiveLogger,
    AdaptiveManager,
    AdaptiveMetrics,
    AdaptivePolicy,
    AdaptiveQueueEntry,
    AdaptiveQueueState,
    AdaptiveRegistry,
    AdaptiveRegistryItem,
    AdaptiveRequest,
    AdaptiveResponse,
    AdaptiveRuleRecord,
    AdaptiveRules,
    AdaptiveSession,
    AdaptiveState,
    AdaptiveValidator,
)
from core.startup_manager import StartupManager
from jarvis import JarvisContext, JarvisCore, JarvisRequest


class AdaptiveTests(unittest.TestCase):
    def test_manager_initializes(self) -> None:
        manager = AdaptiveManager()
        stats = manager.initialize()
        self.assertEqual(stats.overall_adaptive_health, "healthy")
        self.assertTrue(manager.engine.initialized)

    def test_engine_adapts(self) -> None:
        engine = AdaptiveEngine()
        engine.initialize()
        response = engine.adapt(AdaptiveRequest("a1", goal="improve", confidence=0.9))
        self.assertIn("Adaptive review", response.adaptation_report)

    def test_context(self) -> None:
        context = AdaptiveContext("a2")
        self.assertEqual(context.adaptive_id, "a2")

    def test_session(self) -> None:
        self.assertEqual(AdaptiveSession().state, AdaptiveState.CREATED)

    def test_request(self) -> None:
        request = AdaptiveRequest("a3", goal="g")
        self.assertEqual(request.goal, "g")

    def test_response(self) -> None:
        response = AdaptiveResponse("report")
        self.assertEqual(response.adaptation_report, "report")

    def test_policy(self) -> None:
        policy = AdaptivePolicy()
        self.assertTrue(policy.validate(0.8, 0.2))

    def test_rules(self) -> None:
        rules = AdaptiveRules()
        rules.initialize()
        rule = AdaptiveRuleRecord("r1", "reasoning")
        rules.register(rule)
        self.assertIs(rules.lookup("r1"), rule)

    def test_experience(self) -> None:
        experience = AdaptiveExperience()
        experience.initialize()
        record = AdaptiveExperienceRecord("e1", "decision", "good", 0.9)
        experience.register(record)
        self.assertTrue(experience.validate(record))

    def test_learning_queue(self) -> None:
        queue = AdaptiveLearningQueue()
        queue.initialize()
        queue.enqueue(AdaptiveQueueEntry("q1", "a1", AdaptiveQueueState.APPROVED, 5))
        self.assertEqual(queue.entries[0].state, AdaptiveQueueState.APPROVED)

    def test_registry(self) -> None:
        registry = AdaptiveRegistry()
        registry.initialize()
        registry.register(AdaptiveRegistryItem("i1", "experience"))
        self.assertEqual(len(registry.experience_registry), 1)

    def test_history(self) -> None:
        history = AdaptiveHistory()
        history.initialize()
        history.record(AdaptiveHistoryRecord("a1", "approve", 0.9, 0.5, 0.1))
        self.assertEqual(len(history.records), 1)

    def test_metrics(self) -> None:
        metrics = AdaptiveMetrics()
        metrics.initialize()
        self.assertEqual(metrics.requests, 0)

    def test_diagnostics(self) -> None:
        diagnostics = AdaptiveDiagnostics()
        diagnostics.initialize()
        self.assertEqual(diagnostics.summary()["reports"], 0)

    def test_validator(self) -> None:
        validator = AdaptiveValidator()
        validator.initialize()
        self.assertTrue(validator.validate_request(AdaptiveRequest("a4")))

    def test_feedback(self) -> None:
        feedback = AdaptiveFeedback()
        feedback.initialize()
        report = feedback.build(("improve planning",))
        self.assertEqual(report.recommendations[0], "improve planning")

    def test_logger(self) -> None:
        self.assertIsNotNone(AdaptiveLogger().logger)

    def test_startup_includes_adaptive(self) -> None:
        startup = StartupManager()
        startup.start()
        self.assertIsNotNone(startup.adaptive_manager)
        self.assertTrue(startup.adaptive_manager.initialized)

    def test_health_reports_adaptive(self) -> None:
        startup = StartupManager()
        startup.start()
        names = {result.name for result in startup.health_results}
        self.assertIn("adaptive", names)
        self.assertIn("adaptive_engine", names)

    def test_jarvis_context_can_carry_adaptive(self) -> None:
        core = JarvisCore(
            context=JarvisContext(
                request_id="r1",
                metadata={"adaptive_manager": AdaptiveManager()},
            )
        )
        core.initialize()
        response = core.handle(JarvisRequest(content="plan a task"))
        self.assertTrue(response.success)

    def test_component_imports(self) -> None:
        self.assertIsNotNone(AdaptiveManager)
        self.assertIsNotNone(AdaptiveEngine)
        self.assertIsNotNone(AdaptiveExperience)
        self.assertIsNotNone(AdaptivePolicy)
        self.assertIsNotNone(AdaptiveRules)
        self.assertIsNotNone(AdaptiveLearningQueue)
        self.assertIsNotNone(AdaptiveRegistry)
        self.assertIsNotNone(AdaptiveValidator)


def _make_generated_test(index: int):
    def _test(self: AdaptiveTests) -> None:
        manager = AdaptiveManager()
        manager.initialize()
        response = manager.adapt(
            AdaptiveRequest(
                adaptive_id=f"a{index}",
                goal="improve",
                confidence=0.85,
                context={"memory_references": ("m1",)},
            )
        )
        self.assertTrue(response.adaptation_report)
        self.assertGreaterEqual(response.confidence, 0.0)
        self.assertIn(response.executive_recommendation, {"Executive review required"})
        self.assertGreaterEqual(index, 0)

    _test.__name__ = f"test_generated_adaptive_{index:03d}"
    return _test


for _index in range(1, 93):
    setattr(AdaptiveTests, f"test_generated_adaptive_{_index:03d}", _make_generated_test(_index))


if __name__ == "__main__":
    unittest.main()
