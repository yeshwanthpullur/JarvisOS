from __future__ import annotations

import unittest

from commands import CommandManager
from conversation import ConversationContext, ConversationSession
from jarvis.agents import (
    AgentApprovalState,
    AgentCapability,
    AgentCapabilityType,
    AgentExecutionMode,
    AgentRegistry,
    AgentRegistryEntry,
    AgentResultStatus,
    AgentRiskLevel,
    AgentStatus,
    PrimeAgent,
    PrimeDecision,
    PrimeExecutionPlan,
    PrimeRequest,
    PrimeResult,
    classify_intent,
    classify_risk,
    is_execution_allowed,
    requires_approval,
)


def agent(name: str, kind: AgentCapabilityType, ready: bool = True) -> AgentRegistryEntry:
    return AgentRegistryEntry(
        name,
        name,
        "Safe test agent.",
        status=AgentStatus.READY if ready else AgentStatus.UNAVAILABLE,
        capabilities=(AgentCapability(kind.value, kind, "Safe plan-only capability."),),
        enabled=ready,
        health="ready" if ready else "future",
        reason="Ready." if ready else "Future capability is unavailable.",
    )


class Phase3PrimeAgentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = AgentRegistry((
            agent("conversation_agent", AgentCapabilityType.CONVERSATION),
            agent("memory_agent", AgentCapabilityType.MEMORY),
            agent("image_agent", AgentCapabilityType.IMAGE),
            agent("video_agent", AgentCapabilityType.VIDEO),
            agent("communication_agent", AgentCapabilityType.COMMUNICATION, False),
            agent("drone_agent", AgentCapabilityType.DRONE, False),
        ))
        self.prime = PrimeAgent(self.registry)

    def test_models_and_plan_only_default(self) -> None:
        request = PrimeRequest("hello")
        decision = PrimeDecision(request.request_id, AgentCapabilityType.CONVERSATION, "conversation_agent", "conversation")
        plan = PrimeExecutionPlan(request.request_id, "conversation_agent", ("Validate.",))
        result = PrimeResult(request.request_id, decision, plan, AgentResultStatus.PLANNED)
        self.assertEqual(request.requested_execution_mode, AgentExecutionMode.PLAN_ONLY)
        self.assertEqual(result.result_status, AgentResultStatus.PLANNED)

    def test_intent_and_risk_classification(self) -> None:
        cases = {
            "generate an image of a robot": AgentCapabilityType.IMAGE,
            "edit this video": AgentCapabilityType.VIDEO,
            "search memory about robotics": AgentCapabilityType.MEMORY,
            "post this on Instagram": AgentCapabilityType.COMMUNICATION,
            "control my drone": AgentCapabilityType.DRONE,
        }
        for text, expected in cases.items():
            self.assertEqual(classify_intent(text), expected)
        self.assertEqual(classify_risk("control my drone"), AgentRiskLevel.CRITICAL)
        self.assertEqual(classify_risk("post this on Instagram"), AgentRiskLevel.HIGH)

    def test_approval_helpers(self) -> None:
        self.assertTrue(requires_approval(AgentRiskLevel.HIGH, AgentExecutionMode.APPROVED_EXECUTION))
        self.assertFalse(is_execution_allowed(AgentRiskLevel.CRITICAL, AgentExecutionMode.APPROVED_EXECUTION, AgentApprovalState.GRANTED))

    def test_routes_existing_and_future_agents_without_execution(self) -> None:
        self.assertEqual(self.prime.route(PrimeRequest("generate an image of a robot")).selected_agent, "image_agent")
        self.assertEqual(self.prime.route(PrimeRequest("edit this video")).selected_agent, "video_agent")
        self.assertEqual(self.prime.route(PrimeRequest("search memory about robotics")).selected_agent, "memory_agent")
        social = self.prime.route(PrimeRequest("post this on Instagram"))
        self.assertEqual(social.selected_agent, "communication_agent")
        self.assertTrue(social.approval_required)
        self.assertIsNotNone(social.blocked_reason)

    def test_critical_future_agent_is_blocked(self) -> None:
        decision = self.prime.route(PrimeRequest("control my drone"))
        self.assertEqual(decision.execution_mode, AgentExecutionMode.BLOCKED)
        self.assertEqual(decision.risk_level, AgentRiskLevel.CRITICAL)

    def test_plan_has_no_side_effects(self) -> None:
        plan = self.prime.plan(PrimeRequest("edit this video"))
        self.assertEqual(plan.status, AgentResultStatus.PLANNED)
        self.assertTrue(all("execute" not in step.lower() for step in plan.steps))

    def test_prime_cli_commands_are_bounded(self) -> None:
        commands = CommandManager(); commands.initialize()
        context = ConversationContext(session=ConversationSession(), metadata={"agent_registry": self.registry, "prime_agent": self.prime})
        for command in (
            "prime status", 'prime route "generate an image of a robot"', 'prime plan "edit this video"',
            'prime risk "post this on Instagram"', 'prime explain "control my drone"',
        ):
            response = commands.execute(command, context).response
            self.assertTrue(response)
            self.assertLess(len(response), 4000)
            self.assertNotIn("C:\\Users", response)

    def test_prime_config_defaults_are_safe(self) -> None:
        from config import load_settings

        config = load_settings().prime
        self.assertEqual(config.default_execution_mode, "plan_only")
        self.assertTrue(config.block_critical_risk)
        self.assertTrue(config.local_only)


if __name__ == "__main__":
    unittest.main()
