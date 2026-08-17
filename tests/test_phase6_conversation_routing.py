from __future__ import annotations

import unittest

from commands import CommandManager
from conversation import ConversationContext, ConversationRequest, ConversationSession
from conversation.conversation_engine import ConversationEngine
from conversation.conversation_routing import ConversationIntent, classify_conversation_route


class _GoalManager:
    def __init__(self) -> None:
        self.calls = 0

    def prepare_request(self, *_args):
        self.calls += 1
        return type("GoalReport", (), {
            "analysis_type": "goal",
            "summary": "explicit goal",
            "confidence": 1.0,
            "metadata": {},
            "immediate_response": "Goal request accepted.",
        })()


class Phase6ConversationRoutingTests(unittest.TestCase):
    def test_normal_prompts_never_route_to_goal_intelligence(self) -> None:
        prompts = (
            "Who are you?",
            "Tell me a joke.",
            "Explain recursion in one paragraph.",
            "Write one sentence about Python.",
            "What should I do today?",
            "How can I improve JarvisOS?",
            "Give me ideas for my project.",
        )
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                decision = classify_conversation_route(prompt)
                self.assertFalse(decision.goal_routing_allowed)
                self.assertNotIn(decision.intent, {ConversationIntent.GOAL_CREATE, ConversationIntent.GOAL_UPDATE})

    def test_explicit_goal_intents_are_allowed(self) -> None:
        cases = {
            "Create a goal to finish my drone project.": ConversationIntent.GOAL_CREATE,
            "Update my robotics goal.": ConversationIntent.GOAL_UPDATE,
            "Show my goals.": ConversationIntent.GOAL_STATUS,
        }
        for prompt, expected in cases.items():
            with self.subTest(prompt=prompt):
                decision = classify_conversation_route(prompt)
                self.assertEqual(decision.intent, expected)
                self.assertTrue(decision.goal_routing_allowed)

    def test_engine_does_not_invoke_goal_manager_for_chat(self) -> None:
        goals = _GoalManager()
        context = ConversationContext(
            session=ConversationSession(),
            metadata={
                "goal_intelligence_manager": goals,
                "conversation_route": classify_conversation_route("Tell me a joke.").as_metadata(),
            },
        )
        ConversationEngine().handle(ConversationRequest("Tell me a joke.", "tell me a joke."), context)
        self.assertEqual(goals.calls, 0)

    def test_engine_invokes_goal_manager_for_explicit_goal(self) -> None:
        goals = _GoalManager()
        prompt = "Create a goal to finish my drone project."
        context = ConversationContext(
            session=ConversationSession(),
            metadata={
                "goal_intelligence_manager": goals,
                "conversation_route": classify_conversation_route(prompt).as_metadata(),
            },
        )
        response = ConversationEngine().handle(ConversationRequest(prompt, prompt.lower()), context)
        self.assertEqual(goals.calls, 1)
        self.assertEqual(response.response, "Goal request accepted.")

    def test_known_namespace_unknown_subcommand_returns_help(self) -> None:
        manager = CommandManager()
        manager.initialize()
        response = manager.execute("provider unsupported-command")
        self.assertIn("Unknown provider command", response.response)
        self.assertIn("provider status", response.response)

    def test_required_diagnostic_commands_are_registered(self) -> None:
        manager = CommandManager()
        manager.initialize()
        for command in (
            "provider current",
            "conversation diagnostics",
            "conversation route Tell me a joke",
            "goal status",
            "goal route-check Tell me a joke",
            "route inspect Explain recursion",
        ):
            with self.subTest(command=command):
                self.assertNotIn("Unknown command", manager.execute(command).response)

    def test_route_diagnostics_are_bounded_and_explainable(self) -> None:
        manager = CommandManager()
        manager.initialize()
        response = manager.execute("route inspect Tell me a joke")
        self.assertIn("intent=casual", response.response)
        self.assertIn("goal_allowed=no", response.response)
        self.assertLess(len(response.response), 500)


if __name__ == "__main__":
    unittest.main()
