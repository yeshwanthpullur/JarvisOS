from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from commands import CommandManager
from conversation import ConversationContext, ConversationSession
from jarvis.agents import AgentRegistry, PrimeAgent, PrimeRequest, register_specialist_agents
from jarvis.models import ModelRouter, build_default_model_registry
from jarvis.research import (
    ResearchAgent,
    ResearchDepth,
    ResearchEvidence,
    ResearchIntent,
    ResearchPlanner,
    ResearchRiskLevel,
    ResearchSourceType,
    ResearchStatus,
    classify_research_intent,
    classify_research_risk,
    render_research_command,
)
from jarvis.skills import build_default_skill_registry
from config import load_settings


class ResearchFoundationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = ResearchAgent()
        self.commands = CommandManager()
        self.commands.initialize()
        self.agent_registry = register_specialist_agents(AgentRegistry(), vision_ready=True)
        self.model_registry = build_default_model_registry(ollama_ready=True, ollama_models=("llama3.2:1b",), vision_ready=True)
        self.model_router = ModelRouter(self.model_registry)
        self.skill_registry = build_default_skill_registry()
        self.prime = PrimeAgent(self.agent_registry, model_router=self.model_router, skill_registry=self.skill_registry)

    def context(self) -> ConversationContext:
        return ConversationContext(
            session=ConversationSession(),
            metadata={
                "research_agent": self.agent,
                "agent_registry": self.agent_registry,
                "prime_agent": self.prime,
                "model_registry": self.model_registry,
                "model_router": self.model_router,
                "skill_registry": self.skill_registry,
            },
        )

    def test_models_are_typed_and_bounded(self) -> None:
        planner = ResearchPlanner()
        plan = planner.create_plan("compare vLLM and llama.cpp")
        self.assertEqual(plan.research_type, ResearchIntent.COMPARISON)
        self.assertEqual(plan.depth, ResearchDepth.STANDARD)
        self.assertTrue(plan.steps)

    def test_intent_and_risk_classification(self) -> None:
        self.assertEqual(classify_research_intent("compare vLLM and llama.cpp"), ResearchIntent.COMPARISON)
        self.assertEqual(classify_research_risk("find private personal details about a real person", ResearchIntent.WEB_QUESTION), ResearchRiskLevel.BLOCKED)

    def test_safety_policy_blocks_private_person_research(self) -> None:
        response = self.commands.execute('research safety "find private personal details about a real person"', self.context()).response
        self.assertIn("risk=blocked", response)
        self.assertIn("allowed=no", response)

    def test_plan_sources_and_summary_are_bounded(self) -> None:
        plan = self.commands.execute('research plan "compare vLLM and llama.cpp for local JARVIS inference"', self.context()).response
        sources = self.commands.execute('research sources "compare vLLM and llama.cpp for local JARVIS inference"', self.context()).response
        summary = self.commands.execute('research summarize "compare vLLM and llama.cpp for local JARVIS inference"', self.context()).response
        self.assertIn("Research plan:", plan)
        self.assertIn("allowed=", sources)
        self.assertIn("Research summary:", summary)
        self.assertLess(len(plan), 3000)
        self.assertLess(len(sources), 3000)
        self.assertLess(len(summary), 3000)
        plan_id = plan.split("id=", 1)[1].split(" ", 1)[0]
        self.assertIn("status=planned", self.commands.execute(f"research show {plan_id}", self.context()).response)

    def test_evidence_summary_uses_metadata_only(self) -> None:
        evidence = (
            ResearchEvidence("e1", ResearchSourceType.USER, "Local models", "repo", "vLLM and llama.cpp are local model options.", confidence=0.7),
            ResearchEvidence("e2", ResearchSourceType.DOCUMENT, "Docs", "docs/README.md", "The repo documents local-first constraints.", confidence=0.8),
        )
        result = self.agent.summarize("compare vLLM and llama.cpp", evidence)
        self.assertEqual(result.status, ResearchStatus.COMPLETED)
        self.assertIn("user:Local models", result.summary.answer)
        self.assertIn("document:Docs", result.summary.answer)
        self.assertNotIn("C:\\Users", result.summary.answer)

    def test_history_is_bounded_and_persistent_safe(self) -> None:
        for idx in range(3):
            self.agent.summarize(f"research {idx}")
        self.assertEqual(len(self.agent.history), 3)
        with tempfile.TemporaryDirectory() as temp_dir:
            from jarvis.research.storage import ResearchHistoryRecord, ResearchHistoryStore

            store = ResearchHistoryStore(Path(temp_dir), max_records=2)
            store.save((ResearchHistoryRecord("1", "comparison", "planned"), ResearchHistoryRecord("2", "web_question", "completed"), ResearchHistoryRecord("3", "unknown", "blocked")))
            loaded = store.load()
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[-1].request_id, "3")
            stored = store.path.read_text(encoding="utf-8")
            self.assertNotIn("private query", stored)
            self.assertNotIn("query", stored)

    def test_configuration_defaults_are_local_bounded_and_cloud_disabled(self) -> None:
        config = load_settings().research
        self.assertTrue(config.enabled)
        self.assertEqual(config.default_depth, "standard")
        self.assertLessEqual(config.max_plan_steps, 12)
        self.assertLessEqual(config.max_evidence_items, 12)
        self.assertTrue(config.allow_web_read_only)
        self.assertFalse(config.allow_external_search_api)
        self.assertTrue(config.local_only)
        self.assertTrue(config.require_citations_for_web_claims)

    def test_unknown_intent_requests_one_clarification(self) -> None:
        plan = self.agent.plan("blue orange maybe")
        self.assertEqual(plan.status, ResearchStatus.NEEDS_CLARIFICATION)
        self.assertTrue(plan.needs_user_clarification)

    def test_restricted_domain_requires_confirmation_for_action_workflow(self) -> None:
        response = self.commands.execute('research safety "give steps to operate a drone flight controller"', self.context()).response
        self.assertIn("risk=high", response)
        self.assertIn("restricted_domain=safety_critical_engineering", response)
        self.assertIn("confirmation_required=yes", response)

    def test_absolute_source_reference_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "private_source_ref_not_allowed"):
            ResearchEvidence("e1", ResearchSourceType.DOCUMENT, "Private", "C:\\Users\\Example\\secret.txt", "bounded", confidence=0.5)

    def test_web_evidence_without_source_reference_is_not_summarized(self) -> None:
        evidence = (ResearchEvidence("e1", ResearchSourceType.WEB, "Web result", "", "unverified claim", confidence=0.8),)
        result = self.agent.summarize("research local inference", evidence)
        self.assertEqual(result.status, ResearchStatus.UNAVAILABLE)
        self.assertEqual(result.error, "web_evidence_missing_source_ref")
        self.assertIsNone(result.summary)

    def test_secret_shaped_evidence_and_metadata_are_rejected(self) -> None:
        secret_bearing_ref = "https://example.com/?" + "access_" + "token=hidden"
        with self.assertRaisesRegex(ValueError, "secret_shaped_research_evidence_not_allowed"):
            ResearchEvidence("e1", ResearchSourceType.WEB, "Unsafe", secret_bearing_ref, "bounded", confidence=0.5)
        with self.assertRaisesRegex(ValueError, "secret_research_metadata_not_allowed"):
            ResearchEvidence("e2", ResearchSourceType.USER, "Unsafe", "user", "bounded", confidence=0.5, metadata={"secret": "hidden"})

    def test_history_write_failure_is_safe_and_visible(self) -> None:
        store = Mock()
        store.load.return_value = ()
        store.save.side_effect = OSError("unavailable")
        agent = ResearchAgent(history_store=store)
        result = agent.plan_result("compare local model runtimes")
        self.assertEqual(result.status, ResearchStatus.PLANNED)
        self.assertEqual(agent.last_history_error, "RESEARCH_HISTORY_WRITE_FAILED")
        self.assertEqual(agent.status()["history_status"], "error")

    def test_cli_commands_are_available(self) -> None:
        context = self.context()
        for command in (
            "research status",
            "research help",
            'research plan "compare vLLM and llama.cpp for local JARVIS inference"',
            'research safety "compare vLLM and llama.cpp for local JARVIS inference"',
            'research sources "compare vLLM and llama.cpp for local JARVIS inference"',
            'research summarize "compare vLLM and llama.cpp for local JARVIS inference"',
            "research evidence missing",
            "research show missing",
            "research history",
        ):
            response = self.commands.execute(command, context).response
            self.assertTrue(response)
            self.assertLess(len(response), 4000)
            self.assertNotIn("C:\\Users", response)

    def test_prime_routes_to_research_agent(self) -> None:
        decision = self.prime.route(PrimeRequest("research best local model providers for JARVIS"))
        self.assertEqual(decision.selected_agent, "research_agent")
        self.assertIsNone(decision.blocked_reason)

    def test_skill_and_model_integration(self) -> None:
        self.assertIn("research_planning_skill", {item.skill_id for item in self.skill_registry.list_skills()})
        self.assertEqual(self.model_router.route_for_task("research").capability.value, "reasoning")

    def test_agent_registry_exposes_research_agent(self) -> None:
        registry = self.agent_registry
        entry = registry.get_agent("research_agent")
        self.assertIsNotNone(entry)
        self.assertTrue(entry.enabled)
        self.assertIn(entry.health, {"partial_research", "future", "ready"})
        self.assertIn("research", ", ".join(cap.name for cap in entry.capabilities))

    def test_render_command_directly(self) -> None:
        self.assertIn("Research status:", render_research_command(self.agent, "research status", ()))


if __name__ == "__main__":
    unittest.main()
