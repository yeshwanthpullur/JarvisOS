"""Focused tests for Prompt 39 conversation intelligence."""

from __future__ import annotations

import unittest
from types import SimpleNamespace

from conversation import ConversationConfig, ConversationIntelligenceManager, ConversationManager
from jarvis import JarvisResponse


class _Core:
    def __init__(self) -> None:
        self.requests = []

    def handle(self, request):
        self.requests.append(request)
        return JarvisResponse(request_id=request.request_id, content="Mocked conversational answer.", success=True)


class _Memory:
    def __init__(self) -> None:
        self.queries = []
        self.responses = []

    def apply_context(self, query, **kwargs):
        self.queries.append(query)
        return {"memory_context": "bounded preference"}

    def note_response(self, user, response, conversation_id, **kwargs):
        self.responses.append((user, response))


class _Context:
    def __init__(self) -> None:
        self.queries = []

    def prepare_request(self, query, session):
        self.queries.append(query)
        return SimpleNamespace(
            request_type="conversation", status="resolved", confidence=1.0,
            active_objective=None, next_step=None, ambiguity=False,
            stale_reference=False, reason="", pending_state={},
            resolved_item=None, candidates=(), immediate_response=None,
        )

    def record_interaction(self, session, user_input, response):
        return None


class ConversationIntelligenceTests(unittest.TestCase):
    def test_follow_up_keeps_active_topic(self):
        manager = ConversationIntelligenceManager()
        manager.prepare("Explain electric motors.")
        plan = manager.prepare("Go deeper.")
        self.assertEqual(plan.intent, "expand")
        self.assertIn("Active topic: electric motors", plan.provider_input)

    def test_reference_resolves_current_topic(self):
        manager = ConversationIntelligenceManager()
        manager.prepare("Explain the rotor.")
        plan = manager.prepare("How does it work?")
        self.assertIsNone(plan.clarification)
        self.assertGreaterEqual(plan.confidence, 0.8)
        self.assertIn("Active topic: rotor", plan.provider_input)

    def test_ambiguous_comparison_asks_one_clarification(self):
        manager = ConversationIntelligenceManager()
        manager.prepare("Explain induction motors.")
        manager.prepare("Compare with diesel engines.")
        plan = manager.prepare("Is it efficient?")
        self.assertIsNotNone(plan.clarification)
        self.assertEqual(plan.clarification.count("?"), 1)

    def test_explicit_follow_up_applies_to_active_comparison(self):
        manager = ConversationIntelligenceManager()
        manager.prepare("Explain induction motors.")
        manager.prepare("Compare with diesel engines.")
        plan = manager.prepare("Make it shorter.")
        self.assertIsNone(plan.clarification)
        self.assertEqual(plan.intent, "shorten")

    def test_no_context_reference_asks_clarification(self):
        plan = ConversationIntelligenceManager().prepare("Explain it.")
        self.assertEqual(plan.clarification, "What does that refer to?")

    def test_correction_is_detected(self):
        manager = ConversationIntelligenceManager()
        manager.prepare("Compare electric motors with diesel engines.")
        plan = manager.prepare("Actually compare with petrol engines.")
        self.assertEqual(plan.intent, "correction")
        self.assertTrue(plan.interrupted)

    def test_interruption_recovers_cleanly(self):
        manager = ConversationIntelligenceManager()
        manager.prepare("Explain motors.")
        plan = manager.prepare("Wait.")
        self.assertEqual(plan.intent, "interrupt")
        self.assertTrue(plan.interrupted)

    def test_different_question_drops_active_thread(self):
        manager = ConversationIntelligenceManager()
        manager.prepare("Explain motors.")
        manager.prepare("Different question.")
        self.assertIsNone(manager.state.active_topic)

    def test_modes_are_detected(self):
        manager = ConversationIntelligenceManager()
        manager.prepare("Debug this error")
        self.assertEqual(manager.state.mode.value, "debugging")

    def test_context_is_bounded(self):
        manager = ConversationIntelligenceManager(ConversationConfig(max_turns=2, max_context_chars=500))
        for index in range(5):
            manager.prepare(f"Discuss motor design {index}")
            manager.record_response("response")
        self.assertEqual(len(manager.state.turns), 2)
        self.assertLessEqual(len(manager.prepare("Continue").provider_input), 500)

    def test_summary_is_bounded_and_available(self):
        manager = ConversationIntelligenceManager(ConversationConfig(summary_threshold=2))
        for text in ("Explain motors", "Give examples"):
            manager.prepare(text)
            manager.record_response("safe response")
        self.assertIn("Discussed", manager.summary_text())
        self.assertLessEqual(len(manager.summary_text()), 1000)

    def test_reset_does_not_call_memory(self):
        manager = ConversationIntelligenceManager()
        manager.prepare("Explain motors")
        manager.reset()
        self.assertEqual(manager.status_text(), "Conversation: enabled=yes mode=normal topic=none turns=0 confidence=1.00 clarification=none.")

    def test_vision_and_web_context_are_bounded(self):
        manager = ConversationIntelligenceManager()
        plan = manager.prepare("What about it?", {"vision_context": "red car", "web_context": "example page"})
        self.assertIsNotNone(plan.clarification)
        manager.prepare("Describe the red car", {"vision_context": "red car", "web_context": "example page"})
        plan = manager.prepare("Give examples", {"vision_context": "red car", "web_context": "example page"})
        self.assertIn("Vision Context: red car", plan.provider_input)
        self.assertIn("Web Context: example page", plan.provider_input)


class ConversationIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.core = _Core()
        self.memory = _Memory()
        self.manager = ConversationManager(jarvis_core=self.core, memory_intelligence_manager=self.memory)
        self.manager.initialize()

    def test_multi_turn_provider_receives_bounded_context(self):
        self.manager.handle_input("Explain electric motors.")
        response = self.manager.handle_input("Explain the rotor.")
        self.assertEqual(response.response, "Mocked conversational answer.")
        self.assertIn("Recent turns:", self.core.requests[-1].content)

    def test_memory_retrieval_uses_original_words(self):
        self.manager.handle_input("Explain electric motors.")
        self.assertEqual(self.memory.queries[-1], "Explain electric motors.")
        self.assertEqual(self.memory.responses[-1][0], "Explain electric motors.")

    def test_commands_do_not_enter_provider(self):
        response = self.manager.handle_input("conversation status")
        self.assertIn("Conversation: enabled=yes", response.response)
        self.assertEqual(self.core.requests, [])

    def test_conversation_commands(self):
        self.manager.handle_input("Explain motors")
        self.assertIn("Conversation topic:", self.manager.handle_input("conversation topic").response)
        self.assertIn("Conversation confidence:", self.manager.handle_input("conversation confidence").response)
        self.assertIn("Conversation mode:", self.manager.handle_input("conversation mode").response)
        self.assertIn("Discussed", self.manager.handle_input("conversation summary").response)

    def test_reset_keeps_persistent_memory_untouched(self):
        response = self.manager.handle_input("conversation reset")
        self.assertIn("Persistent memory was not changed", response.response)
        self.assertEqual(self.memory.responses, [])

    def test_clarification_does_not_call_provider(self):
        response = self.manager.handle_input("Explain it.")
        self.assertEqual(response.response, "What does that refer to?")
        self.assertEqual(self.core.requests, [])

    def test_voice_transcript_uses_same_handle_input_path(self):
        self.manager.handle_input("Explain motors")
        response = self.manager.handle_input("Continue.", request_id="voice-request")
        self.assertEqual(response.response, "Mocked conversational answer.")
        self.assertEqual(self.core.requests[-1].request_id, "voice-request")

    def test_session_exposes_active_topic(self):
        self.manager.handle_input("Explain induction motors")
        self.assertEqual(self.manager.active_session.current_topic, "induction motors")

    def test_context_intelligence_receives_original_follow_up(self):
        context = _Context()
        manager = ConversationManager(jarvis_core=self.core, context_intelligence_manager=context)
        manager.initialize()
        manager.handle_input("Explain motors")
        manager.handle_input("Make it shorter")
        self.assertEqual(context.queries[-1], "Make it shorter")


if __name__ == "__main__":
    unittest.main()
