from __future__ import annotations

import unittest

from commands import CommandManager
from conversation import ConversationContext, ConversationSession
from jarvis.agents import (
    AgentCapability,
    AgentCapabilityType,
    AgentDecision,
    AgentExecutionMode,
    AgentRegistry,
    AgentRegistryEntry,
    AgentRegistryError,
    AgentRequest,
    AgentResult,
    AgentResultStatus,
    AgentRiskLevel,
    AgentStatus,
)


def entry(name: str = "conversation_agent", enabled: bool = True) -> AgentRegistryEntry:
    return AgentRegistryEntry(
        name=name,
        display_name=name.replace("_", " ").title(),
        description="Bounded local conversation metadata.",
        status=AgentStatus.READY if enabled else AgentStatus.DISABLED,
        enabled=enabled,
        health="ready" if enabled else "disabled",
        reason="Verified local foundation." if enabled else "Disabled by policy.",
        capabilities=(AgentCapability("conversation", AgentCapabilityType.CONVERSATION, "Safe conversation routing."),),
    )


class Phase3AgentRegistryTests(unittest.TestCase):
    def test_protocol_models_are_bounded_and_typed(self) -> None:
        request = AgentRequest("hello", "conversation", AgentCapabilityType.CONVERSATION)
        decision = AgentDecision(request.request_id, "conversation_agent", "conversation", confidence=0.9)
        result = AgentResult(request.request_id, "conversation_agent", "conversation", AgentResultStatus.PLANNED, "plan")
        self.assertEqual(request.execution_mode, AgentExecutionMode.PLAN_ONLY)
        self.assertEqual(decision.selected_agent, "conversation_agent")
        self.assertEqual(result.status, AgentResultStatus.PLANNED)

    def test_side_effects_require_approval(self) -> None:
        with self.assertRaises(ValueError):
            AgentCapability("write", AgentCapabilityType.SYSTEM, "write", side_effects=("files",))

    def test_duplicate_agent_is_rejected(self) -> None:
        registry = AgentRegistry((entry(),))
        with self.assertRaises(AgentRegistryError):
            registry.register_agent(entry())

    def test_duplicate_capability_is_rejected(self) -> None:
        capability = AgentCapability("chat", AgentCapabilityType.CONVERSATION, "chat")
        with self.assertRaises(ValueError):
            AgentRegistryEntry("a", "A", "A", capabilities=(capability, capability))

    def test_disabled_agent_is_not_executable_candidate(self) -> None:
        registry = AgentRegistry((entry(enabled=False),))
        self.assertEqual(registry.find_by_capability("conversation"), ())
        self.assertEqual(len(registry.find_by_capability("conversation", executable_only=False)), 1)

    def test_diagnostics_and_validation(self) -> None:
        registry = AgentRegistry((entry(),))
        self.assertEqual(registry.validate_registry(), ())
        self.assertTrue(registry.registry_summary()["valid"])

    def test_cli_agent_commands(self) -> None:
        registry = AgentRegistry((entry(),))
        commands = CommandManager(); commands.initialize()
        context = ConversationContext(session=ConversationSession(), metadata={"agent_registry": registry})
        for command in ("agent status", "agent list", "agent capabilities", "agent show conversation_agent", "agent find conversation", "agent diagnostics"):
            response = commands.execute(command, context).response
            self.assertTrue(response)
            self.assertLess(len(response), 4000)
            self.assertNotIn("C:\\Users", response)

    def test_config_defaults_are_safe(self) -> None:
        from config import load_settings

        settings = load_settings()
        self.assertEqual(settings.agents.default_mode, "plan_only")
        self.assertTrue(settings.agents.local_only_default)
        self.assertTrue(settings.agents.require_approval_for_high_risk)


if __name__ == "__main__":
    unittest.main()
