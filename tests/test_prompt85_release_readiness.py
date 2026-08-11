import json
import re
import unittest
from pathlib import Path

from commands import CommandManager
from jarvis.release_readiness import GateState, ReleaseGate, ReleaseReadinessEvaluator


ROOT = Path(__file__).parents[1]
COMMANDS = (
    "status", "gates", "contracts", "missing", "candidate", "matrix",
    "scenarios", "scorecard", "checklist", "verify", "help",
)


class Prompt85ReleaseReadinessTests(unittest.TestCase):
    def setUp(self):
        self.evaluator = ReleaseReadinessEvaluator(ROOT)

    def test_gate_model_is_bounded(self):
        gate = ReleaseGate("x" * 200, "category", GateState.WARNING, False, "owner", ("e" * 500,))
        self.assertLessEqual(len(gate.gate_id), 80)
        self.assertLessEqual(len(gate.evidence[0]), 240)

    def test_all_phase5_components_are_detected(self):
        report = self.evaluator.evaluate()
        self.assertEqual(report.missing_components, ())
        self.assertTrue(report.mandatory_passed)
        self.assertEqual(report.status, GateState.WARNING)

    def test_warning_is_only_a_nonblocking_release_checkpoint(self):
        report = self.evaluator.evaluate()
        blocking = [gate for gate in report.gates if gate.blocking]
        self.assertTrue(blocking)
        self.assertTrue(all(gate.status is GateState.PASSED for gate in blocking))
        self.assertTrue(any(gate.gate_id == "release" and not gate.blocking for gate in report.gates))

    def test_authorities_remain_independent(self):
        contracts = {item.component: item for item in self.evaluator.contracts()}
        self.assertEqual(contracts["Execution Policy"].authority, "action policy authority")
        self.assertEqual(contracts["Approval System"].authority, "exact authorization authority")
        self.assertEqual(contracts["Execution Broker"].authority, "execution dispatch authority")
        self.assertIn("direct execution", contracts["Prime Agent"].unsupported_interactions)
        self.assertIn("execute", contracts["Enterprise Governance"].unsupported_interactions)

    def test_contract_inventory_is_complete_and_passed(self):
        contracts = self.evaluator.contracts()
        self.assertEqual(len(contracts), 21)
        self.assertTrue(all(item.verification_status is GateState.PASSED for item in contracts))
        self.assertEqual(len({item.component for item in contracts}), len(contracts))

    def test_compatibility_matrix_is_bounded(self):
        matrix = self.evaluator.compatibility()
        self.assertEqual(len(matrix), 15)
        self.assertTrue(all(item.status in {"supported", "restricted"} for item in matrix))
        self.assertTrue(any(item.source == "Workflow" and item.target == "Approval" for item in matrix))

    def test_end_to_end_scenarios_are_declared(self):
        scenarios = self.evaluator.scenarios()
        self.assertEqual(len(scenarios), 14)
        self.assertTrue(all(item.status is GateState.PASSED for item in scenarios))
        self.assertIn("zero-trust", {item.scenario_id for item in scenarios})

    def test_scorecard_is_conservative_and_valid(self):
        scorecard = self.evaluator.scorecard()
        self.assertEqual(len(scorecard), 11)
        self.assertTrue(all(0 <= item.score <= 100 for item in scorecard))
        self.assertLess(max(item.score for item in scorecard), 100)

    def test_candidate_does_not_create_release(self):
        candidate = self.evaluator.candidate()
        self.assertEqual(candidate.version, "v2.0.0")
        self.assertEqual(candidate.status, GateState.WARNING)
        self.assertFalse(candidate.blocking_gate_ids)

    def test_vercel_contract_remains_status_only(self):
        api = (ROOT / "api" / "index.py").read_text(encoding="utf-8")
        for forbidden in ("ExecutionBroker", "FileExecutor", "ModelRouter", "Telegram", "MCPRuntime"):
            self.assertNotIn(forbidden, api)

    def test_configuration_disables_release_side_effects(self):
        text = (ROOT / "config.yaml").read_text(encoding="utf-8")
        self.assertIn("release_readiness:", text)
        self.assertIn("allow_tag_creation: false", text)
        self.assertIn("allow_release_creation: false", text)
        self.assertIn("allow_deployment: false", text)

    def test_cli_commands_are_bounded_and_truthful(self):
        manager = CommandManager(); manager.initialize()
        for operation in COMMANDS:
            with self.subTest(operation=operation):
                response = manager.execute(f"release-readiness {operation}").response
                self.assertLess(len(response), 8000)
                self.assertNotIn("Unknown command", response)
                self.assertIsNone(re.search(r"[A-Za-z]:\\Users\\", response))
        self.assertIn("status=warning", manager.execute("release-readiness status").response)
        self.assertIn("tag_created=no", manager.execute("release-readiness candidate").response)
        self.assertIn("mandatory_passed=yes", manager.execute("release-readiness verify").response)

    def test_project_health_json_records_validation_without_release(self):
        health = json.loads((ROOT / "docs" / "project_health.json").read_text(encoding="utf-8"))
        phase = health["phase5_validation"]
        self.assertFalse(phase["v2_tag_created"])
        self.assertFalse(phase["github_release_created"])
        self.assertFalse(phase["phase6_started"])


if __name__ == "__main__":
    unittest.main()
