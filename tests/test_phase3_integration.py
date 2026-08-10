"""Cross-foundation safety and status tests for Phase 3."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from commands import CommandManager


ROOT = Path(__file__).resolve().parents[1]


class Phase3IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.commands = CommandManager()
        self.commands.initialize()

    def execute(self, value: str) -> str:
        response = self.commands.execute(value).response
        self.assertLess(len(response), 4_000)
        self.assertNotRegex(response, r"[A-Za-z]:\\")
        self.assertNotRegex(response, r"(?i)(api[_-]?key|password|access[_-]?token|secret)\s*[:=]\s*\S+")
        return response

    def test_agent_prime_model_and_skill_status_are_available(self) -> None:
        self.assertIn("mode=plan_only", self.execute("agent status"))
        self.assertIn("default_mode=plan_only", self.execute("prime status"))
        self.assertIn("local_only_default=true", self.execute("model status"))
        self.assertIn("Skill Registry", self.execute("skill status"))

    def test_prime_routes_without_claiming_execution(self) -> None:
        image = self.execute('prime route "generate an image of a robot"')
        self.assertIn("agent=image_agent", image)
        self.assertIn("mode=plan_only", image)
        social = self.execute('prime risk "post this on Instagram"')
        self.assertIn("approval_required=yes", social)
        drone = self.execute('prime explain "control my drone"')
        self.assertIn("agent=drone_agent", drone)
        self.assertIn("Critical-risk execution is blocked", drone)

    def test_model_policy_blocks_cloud_and_reports_future_routes(self) -> None:
        policy = self.execute("model policy")
        self.assertIn("cloud_providers=disabled", policy)
        providers = self.execute("model providers")
        self.assertIn("nemotron", providers.lower())
        self.assertNotIn("nemotron:ready", providers.lower())

    def test_skill_policy_keeps_mcp_and_external_actions_disabled(self) -> None:
        skills = self.execute("skill list")
        self.assertIn("mcp_gateway_skill:future", skills)
        self.assertIn("telegram_skill:future", skills)
        diagnostics = self.execute("skill diagnostics")
        self.assertIn("valid=True", diagnostics)

    def test_project_status_contains_bounded_phase3_summary(self) -> None:
        response = self.commands.execute("project status")
        self.assertIn("phase3=agents:", response.response)
        self.assertEqual(response.metadata["total_agents"], 29)
        self.assertEqual(response.metadata["prime_agent_status"], "ready")
        self.assertEqual(response.metadata["model_router_status"], "ready")
        self.assertEqual(response.metadata["skill_registry_status"], "ready")
        self.assertEqual(response.metadata["research_agent_status"], "partial")

    def test_vercel_metadata_remains_status_only(self) -> None:
        source = (ROOT / "api" / "index.py").read_text(encoding="utf-8")
        self.assertIn('"multi_agent_os": "partial_plan_only_foundation"', source)
        self.assertNotIn("PrimeAgent(", source)
        self.assertNotIn("ModelRouter(", source)
        self.assertNotIn("SkillRegistry(", source)
        self.assertNotIn("ResearchAgent(", source)
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        self.assertNotIn("main.py", json.dumps(config))

    def test_main_remains_cli_only(self) -> None:
        source = (ROOT / "main.py").read_text(encoding="utf-8")
        self.assertIn("def main", source)
        self.assertIsNone(re.search(r"^(app|application|handler)\s*=", source, re.MULTILINE))


if __name__ == "__main__":
    unittest.main()
