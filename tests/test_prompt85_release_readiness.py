import json
import re
import unittest
from pathlib import Path

from commands import CommandManager
from jarvis.release_readiness import GateState, ReleaseGate, ReleaseReadinessEvaluator


ROOT = Path(__file__).parents[1]


class Prompt85ReleaseReadinessTests(unittest.TestCase):
    def setUp(self):
        self.evaluator = ReleaseReadinessEvaluator(ROOT)

    def test_gate_model_is_bounded(self):
        gate = ReleaseGate("x" * 200, "category", GateState.WARNING, False, "owner", ("e" * 500,))
        self.assertLessEqual(len(gate.gate_id), 80)
        self.assertLessEqual(len(gate.evidence[0]), 240)

    def test_missing_phase5_components_block_release(self):
        report = self.evaluator.evaluate()
        self.assertEqual(report.status, GateState.BLOCKED)
        self.assertNotIn("external_integration_control_plane", report.missing_components)
        self.assertIn("enterprise_governance", report.missing_components)
        self.assertGreater(report.blocked, 0)

    def test_phase4_authorities_remain_passed(self):
        report = self.evaluator.evaluate()
        contracts = {item.component: item for item in report.contracts}
        self.assertEqual(contracts["Execution Policy"].authority, "action policy authority")
        self.assertEqual(contracts["Approval System"].authority, "exact authorization authority")
        self.assertEqual(contracts["Execution Broker"].authority, "execution dispatch authority")
        self.assertIn("direct execution", contracts["Prime Agent"].unsupported_interactions)

    def test_candidate_is_blocked_and_does_not_create_release(self):
        candidate = self.evaluator.candidate()
        self.assertEqual(candidate.version, "v2.0.0")
        self.assertEqual(candidate.status, GateState.BLOCKED)
        self.assertTrue(candidate.blocking_gate_ids)

    def test_vercel_contract_remains_status_only(self):
        api = (ROOT / "api" / "index.py").read_text(encoding="utf-8")
        for forbidden in ("ExecutionBroker", "FileExecutor", "ModelRouter", "Telegram", "MCP"):
            self.assertNotIn(forbidden, api)

    def test_configuration_disables_release_side_effects(self):
        text = (ROOT / "config.yaml").read_text(encoding="utf-8")
        self.assertIn("release_readiness:", text)
        self.assertIn("allow_tag_creation: false", text)
        self.assertIn("allow_release_creation: false", text)
        self.assertIn("allow_deployment: false", text)

    def test_cli_commands_are_bounded_and_truthful(self):
        manager = CommandManager(); manager.initialize()
        for command in ("release-readiness status", "release-readiness gates", "release-readiness contracts", "release-readiness missing", "release-readiness candidate", "release-readiness help"):
            with self.subTest(command=command):
                response = manager.execute(command).response
                self.assertLess(len(response), 8000)
                self.assertNotIn("Unknown command", response)
                self.assertIsNone(re.search(r"[A-Za-z]:\\Users\\", response))
        self.assertIn("status=blocked", manager.execute("release-readiness status").response)
        self.assertIn("tag_created=no", manager.execute("release-readiness candidate").response)

    def test_project_health_json_remains_valid(self):
        health = json.loads((ROOT / "docs" / "project_health.json").read_text(encoding="utf-8"))
        self.assertIn("overall_mvp_readiness", health)


if __name__ == "__main__":
    unittest.main()
