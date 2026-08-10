from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

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
            store.save((ResearchHistoryRecord("1", "a", "planned"), ResearchHistoryRecord("2", "b", "completed"), ResearchHistoryRecord("3", "c", "blocked")))
            loaded = store.load()
            self.assertEqual(len(loaded), 2)
            self.assertEqual(loaded[-1].request_id, "3")

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

    def test_skill_and_model_integration(self) -> None:
        self.assertIn("research_planning_skill", {item.skill_id for item in self.skill_registry.list_skills()})
        self.assertEqual(self.model_router.route_for_task("research").capability.value, "reasoning")

    def test_agent_registry_exposes_research_agent(self) -> None:
        registry = self.agent_registry
        entry = registry.get_agent("research_agent")
        self.assertIsNotNone(entry)
        self.assertIn(entry.health, {"partial_research", "future", "ready"})
        self.assertIn("research", ", ".join(cap.name for cap in entry.capabilities))

    def test_render_command_directly(self) -> None:
        self.assertIn("Research status:", render_research_command(self.agent, "research status", ()))


if __name__ == "__main__":
    unittest.main()
