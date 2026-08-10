from __future__ import annotations

import unittest

from commands import CommandManager
from conversation import ConversationContext, ConversationSession
from jarvis.agents import (
    AgentCapabilityType, AgentExecutionMode, AgentRegistry, AgentRiskLevel,
    AgentStatus, PrimeAgent, PrimeRequest, register_specialist_agents,
)
from jarvis.models import ModelRouter, build_default_model_registry
from jarvis.skills import build_default_skill_registry


class Phase3SpecialistAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.agent_registry = register_specialist_agents(AgentRegistry(), vision_ready=True)
        self.model_registry = build_default_model_registry(ollama_ready=True, ollama_models=("llama3.2:1b", "llava:latest"), vision_ready=True)
        self.model_router = ModelRouter(self.model_registry)
        self.skill_registry = build_default_skill_registry()
        self.prime = PrimeAgent(self.agent_registry, model_router=self.model_router, skill_registry=self.skill_registry)

    def test_existing_and_foundation_agents_are_truthful(self) -> None:
        self.assertEqual(self.agent_registry.get_agent("conversation_agent").status, AgentStatus.READY)
        self.assertEqual(self.agent_registry.get_agent("image_agent").health, "workflow_foundation")
        self.assertEqual(self.agent_registry.get_agent("video_agent").health, "workflow_foundation")
        self.assertEqual(self.agent_registry.get_agent("web_agent").health, "partial_read_only")
        self.assertEqual(self.agent_registry.get_agent("sync_agent").health, "partial_local_queue")

    def test_future_agents_are_unavailable(self) -> None:
        self.assertEqual(self.agent_registry.get_agent("communication_agent").health, "draft_only")
        self.assertEqual(self.agent_registry.get_agent("communication_agent").status, AgentStatus.READY)
        for name in ("robotics_agent", "drone_agent", "social_media_agent"):
            entry = self.agent_registry.get_agent(name)
            self.assertEqual(entry.status, AgentStatus.UNAVAILABLE)
            self.assertFalse(entry.enabled)
            self.assertEqual(entry.health, "future")

    def test_high_risk_and_approval_capabilities(self) -> None:
        drone = self.agent_registry.get_agent("drone_agent").capabilities[0]
        self.assertEqual(drone.risk_level, AgentRiskLevel.CRITICAL)
        self.assertTrue(drone.requires_approval)

    def test_prime_routes_to_truthful_specialists(self) -> None:
        self.assertEqual(self.prime.route(PrimeRequest("generate an image of a robot")).selected_agent, "image_agent")
        self.assertEqual(self.prime.route(PrimeRequest("edit this video")).selected_agent, "video_agent")
        self.assertEqual(self.prime.route(PrimeRequest("search memory about robotics")).selected_agent, "memory_agent")
        communication = self.prime.route(PrimeRequest("post this on Instagram"))
        self.assertEqual(communication.selected_agent, "communication_agent")
        self.assertIsNotNone(communication.blocked_reason)
        drone = self.prime.route(PrimeRequest("control my drone"))
        self.assertEqual(drone.execution_mode, AgentExecutionMode.BLOCKED)

    def test_model_and_skill_declarations_are_connected(self) -> None:
        image = self.prime.route(PrimeRequest("generate an image of a robot"))
        self.assertIsNotNone(image.selected_model_route)
        self.assertIs(self.prime.skill_registry, self.skill_registry)

    def test_diagnostic_cli_has_no_side_effects(self) -> None:
        commands = CommandManager(); commands.initialize()
        context = ConversationContext(session=ConversationSession(), metadata={
            "agent_registry": self.agent_registry, "prime_agent": self.prime,
            "model_registry": self.model_registry, "model_router": self.model_router,
            "skill_registry": self.skill_registry,
        })
        for command in ("agent ready", "agent unavailable", "agent future", "agent risks", "agent approvals"):
            response = commands.execute(command, context).response
            self.assertTrue(response)
            self.assertLess(len(response), 6000)
            self.assertNotIn("C:\\Users", response)


if __name__ == "__main__":
    unittest.main()
