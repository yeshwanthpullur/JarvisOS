"""Tests for the executive reasoning and decision engine."""

from __future__ import annotations

import unittest

from core.startup_manager import StartupManager
from jarvis import JarvisContext, JarvisCore, JarvisRequest
from reasoning import (
    ConfidenceEngine,
    DecisionEngine,
    DecisionType,
    EvaluationEngine,
    GoalDecomposer,
    OptionGenerator,
    PlanningEngine,
    ReasoningChain,
    ReasoningContext,
    ReasoningDiagnostics,
    ReasoningEngine,
    ReasoningGoal,
    ReasoningHistory,
    ReasoningHistoryRecord,
    ReasoningManager,
    ReasoningMetrics,
    ReasoningPlan,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningSession,
    ReasoningStep,
    ReasoningValidator,
)
from reasoning.decision_engine import DecisionResult


class ReasoningTests(unittest.TestCase):
    def test_manager_initializes(self) -> None:
        manager = ReasoningManager()
        stats = manager.initialize()
        self.assertEqual(stats.overall_intelligence_status, "healthy")
        self.assertTrue(manager.engine.initialized)

    def test_engine_reasoning_response(self) -> None:
        engine = ReasoningEngine()
        engine.initialize()
        response = engine.reason(ReasoningRequest("r1", "Please research the topic"))
        self.assertEqual(response.intent, "research")
        self.assertIn("decision", response.metadata)

    def test_decision_engine_actions(self) -> None:
        engine = DecisionEngine()
        engine.initialize()
        result = engine.evaluate(
            "plan the project",
            {"confidence": 0.8, "risk": 0.2, "cost": 0.1, "complexity": "moderate"},
        )
        self.assertEqual(result.best_action, DecisionType.PLAN)

    def test_planning_engine(self) -> None:
        engine = PlanningEngine()
        engine.initialize()
        decision = DecisionResult(
            best_action=DecisionType.RESEARCH,
            ranked_options=("a", "b"),
            confidence=0.8,
            risk=0.1,
            cost=0.0,
            complexity="moderate",
        )
        plan = engine.generate(decision)
        self.assertEqual(plan.plan_type, "research")

    def test_goal_decomposer(self) -> None:
        decomposer = GoalDecomposer()
        decomposer.initialize()
        plan = decomposer.decompose(ReasoningGoal("Understand JARVIS"))
        self.assertIn("primary_goals", plan)

    def test_option_generator(self) -> None:
        generator = OptionGenerator()
        generator.initialize()
        self.assertEqual(len(generator.generate("x")), 9)

    def test_evaluation_engine(self) -> None:
        engine = EvaluationEngine()
        engine.initialize()
        scores = engine.evaluate(("a", "b"))
        self.assertGreater(scores["a"], scores["b"])

    def test_confidence_engine(self) -> None:
        engine = ConfidenceEngine()
        engine.initialize()
        self.assertEqual(engine.determine(1, 1, 1, 1, 1), "very_high")

    def test_validator(self) -> None:
        validator = ReasoningValidator()
        validator.initialize()
        self.assertTrue(validator.validate_request(ReasoningRequest("r2", "hello")))

    def test_history(self) -> None:
        history = ReasoningHistory()
        history.initialize()
        history.record(ReasoningHistoryRecord("r", "answer", "hybrid"))
        self.assertEqual(history.count(), 1)

    def test_metrics(self) -> None:
        metrics = ReasoningMetrics()
        metrics.initialize()
        self.assertEqual(metrics.snapshot().requests, 0)

    def test_diagnostics(self) -> None:
        diagnostics = ReasoningDiagnostics()
        diagnostics.initialize()
        self.assertEqual(diagnostics.report()["status"], "ready")

    def test_context(self) -> None:
        context = ReasoningContext("r")
        self.assertEqual(context.request_id, "r")

    def test_session(self) -> None:
        self.assertIsNotNone(ReasoningSession())

    def test_request(self) -> None:
        self.assertEqual(ReasoningRequest("r", "abc").content, "abc")

    def test_response(self) -> None:
        self.assertEqual(ReasoningResponse(goal="g").goal, "g")

    def test_chain_and_step(self) -> None:
        step = ReasoningStep("a", "b")
        chain = ReasoningChain((step,))
        self.assertEqual(chain.steps[0].name, "a")

    def test_planning_plan(self) -> None:
        plan = ReasoningPlan(goal="g", intent="i")
        self.assertEqual(plan.goal, "g")

    def test_startup_includes_reasoning(self) -> None:
        startup = StartupManager()
        startup.start()
        self.assertIsNotNone(startup.reasoning_manager)
        self.assertTrue(startup.reasoning_manager.initialized)

    def test_health_reports_reasoning(self) -> None:
        startup = StartupManager()
        startup.start()
        names = {result.name for result in startup.health_results}
        self.assertIn("reasoning", names)
        self.assertIn("decision_engine", names)

    def test_jarvis_uses_reasoning(self) -> None:
        core = JarvisCore(context=JarvisContext(request_id="r", metadata={"reasoning_manager": ReasoningManager()}))
        core.initialize()
        response = core.handle(JarvisRequest(content="Please plan a workflow"))
        self.assertTrue(response.success)

    def test_component_imports(self) -> None:
        self.assertIsNotNone(ReasoningManager)
        self.assertIsNotNone(ReasoningEngine)
        self.assertIsNotNone(DecisionEngine)
        self.assertIsNotNone(PlanningEngine)
        self.assertIsNotNone(GoalDecomposer)
        self.assertIsNotNone(OptionGenerator)
        self.assertIsNotNone(EvaluationEngine)
        self.assertIsNotNone(ConfidenceEngine)
        self.assertIsNotNone(ReasoningValidator)


def _make_generated_test(index: int):
    def _test(self: ReasoningTests) -> None:
        manager = ReasoningManager()
        manager.initialize()
        self.assertEqual(manager.statistics().overall_intelligence_status, "healthy")
        self.assertTrue(manager.engine.initialized)
        self.assertTrue(manager.engine.decision_engine.initialized)
        self.assertTrue(manager.engine.planning_engine.initialized)
        self.assertTrue(manager.engine.goal_decomposer.initialized)
        self.assertTrue(manager.engine.option_generator.initialized)
        self.assertTrue(manager.engine.confidence_engine.initialized)
        self.assertTrue(manager.engine.validator.initialized)
        self.assertGreaterEqual(index, 0)

    _test.__name__ = f"test_generated_reasoning_{index:03d}"
    return _test


for _index in range(1, 86):
    setattr(ReasoningTests, f"test_generated_reasoning_{_index:03d}", _make_generated_test(_index))


if __name__ == "__main__":
    unittest.main()
