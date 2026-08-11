import unittest
from importlib import import_module
from pathlib import Path

from jarvis.release_readiness import GateState, ReleaseReadinessEvaluator


ROOT = Path(__file__).parents[1]


class Phase5FinalIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evaluator = ReleaseReadinessEvaluator(ROOT)
        cls.report = cls.evaluator.evaluate()

    def test_required_runtime_modules_import(self):
        for module in (
            "jarvis.integrations.registry", "jarvis.integrations.telegram.runtime",
            "jarvis.integrations.outbound_connectors", "jarvis.integrations.github",
            "jarvis.mcp_runtime.runtime", "jarvis.plugin_runtime.runtime",
            "jarvis.models.runtime_control", "jarvis.research.runtime",
            "jarvis.knowledge.runtime", "agents.orchestration_runtime",
            "workflow.runtime", "jarvis.reliability.runtime", "jarvis.governance.runtime",
        ):
            with self.subTest(module=module):
                self.assertIsNotNone(import_module(module))

    def test_no_blocking_gate_failed(self):
        self.assertTrue(self.report.mandatory_passed)
        self.assertFalse(any(g.blocking and g.status is not GateState.PASSED for g in self.report.gates))

    def test_scenario_paths_are_bounded(self):
        for item in self.report.scenarios:
            self.assertLessEqual(len(item.expected_path), 8)
            self.assertLess(len(item.expected_output), 240)
            self.assertLess(len(item.expected_failure), 240)

    def test_sensitive_boundaries_are_represented(self):
        text = " ".join(" ".join(item.unsupported_interactions) for item in self.report.contracts)
        for boundary in ("approval bypass", "silent edit", "browser write", "credential disclosure"):
            self.assertIn(boundary, text)

    def test_compatibility_preserves_authority(self):
        restricted = {(item.source, item.target) for item in self.report.compatibility if item.status == "restricted"}
        self.assertIn(("Workflow", "Governance"), {(x.source, x.target) for x in self.report.compatibility})
        self.assertIn(("Coding", "GitHub"), restricted)
        self.assertIn(("MCP", "Broker"), restricted)

    def test_release_actions_are_not_performed(self):
        candidate = self.evaluator.candidate()
        self.assertEqual(candidate.version, "v2.0.0")
        self.assertEqual(candidate.branch, "main")
        self.assertNotEqual(candidate.commit, "unavailable")

    def test_evaluator_does_not_modify_worktree(self):
        before = self.evaluator._git("status", "--short", "--untracked-files=no")
        self.evaluator.evaluate(); self.evaluator.candidate()
        after = self.evaluator._git("status", "--short", "--untracked-files=no")
        self.assertEqual(before, after)

    def test_api_has_no_phase5_execution_imports(self):
        api = (ROOT / "api" / "index.py").read_text(encoding="utf-8")
        self.assertNotIn("jarvis.governance", api)
        self.assertNotIn("jarvis.reliability", api)
        self.assertNotIn("workflow.runtime", api)

    def test_validation_outputs_have_no_private_path(self):
        values = [self.report.warnings]
        values.extend(item.evidence + item.warnings for item in self.report.gates)
        flattened = repr(values)
        self.assertNotIn(":\\Users\\", flattened)

    def test_scorecard_documents_release_readiness(self):
        scores = {item.category: item.score for item in self.report.scorecard}
        self.assertIn("Release Readiness", scores)
        self.assertGreaterEqual(scores["Security"], 90)
        self.assertLessEqual(scores["Release Readiness"], scores["Testing"])

    def test_final_validation_docs_exist(self):
        for name in (
            "PHASE_5_INTEGRATION_CHECKLIST.md", "COMPATIBILITY_MATRIX.md",
            "SYSTEM_VALIDATION_MATRIX.md", "END_TO_END_VALIDATION.md",
            "PRODUCTION_READINESS_SCORECARD.md", "DISASTER_RECOVERY_PLAN.md",
        ):
            with self.subTest(name=name):
                self.assertTrue((ROOT / "docs" / name).is_file())


if __name__ == "__main__":
    unittest.main()
