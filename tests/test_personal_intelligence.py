"""Tests for Personal Intelligence integration."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from commands import CommandManager
from conversation import ConversationContext, ConversationManager, ConversationRequest, ConversationSession
from jarvis import JarvisCore
from memory import MemoryManager
from personal_intelligence import PersonalClassification, PersonalIntelligenceManager
from retrieval import RetrievalManager
from core.health_checker import HealthChecker
from core.startup_manager import StartupManager


class PersonalIntelligenceTests(unittest.TestCase):
    """Behavioral tests for personal intelligence."""

    def _manager(self) -> tuple[MemoryManager, PersonalIntelligenceManager]:
        memory = MemoryManager(Path(self.tempdir.name))
        memory.initialize()
        personal = PersonalIntelligenceManager(memory_manager=memory, retrieval_manager=RetrievalManager())
        personal.initialize()
        return memory, personal

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_capture_explicit_preference_from_statement(self) -> None:
        memory, personal = self._manager()
        captured = personal.detect_candidates("I prefer concise answers.")
        self.assertEqual(len(captured), 1)
        self.assertEqual(captured[0].category, "communication preference")
        self.assertEqual(memory.count_memories(), 1)

    def test_retrieve_active_personal_information(self) -> None:
        _, personal = self._manager()
        captured = personal.detect_candidates("I prefer concise answers.")[0]
        result = personal.retrieve("answer-length preference")
        self.assertTrue(result.items)
        self.assertEqual(result.items[0].item_id, captured.item_id)
        self.assertEqual(result.items[0].classification, PersonalClassification.EXPLICIT)

    def test_explain_returns_provenance(self) -> None:
        _, personal = self._manager()
        captured = personal.detect_candidates("I prefer concise answers.")[0]
        explanation = personal.explain(captured.item_id)
        self.assertIsNotNone(explanation)
        self.assertEqual(explanation["source_type"], "direct_user_statement")

    def test_update_supersedes_previous_value(self) -> None:
        _, personal = self._manager()
        first = personal.detect_candidates("I prefer concise answers.")[0]
        second = personal.supersede(
            first.item_id,
            "detailed answers",
            source_type="direct_user_statement",
            source_reference="conversation-2",
            confidence=0.95,
        )
        self.assertIsNotNone(second)
        active = personal.retrieve("answers")
        self.assertEqual(len(active.items), 1)
        self.assertEqual(active.items[0].value, "detailed answers")

    def test_forget_removes_active_context(self) -> None:
        _, personal = self._manager()
        captured = personal.detect_candidates("I prefer concise answers.")[0]
        self.assertTrue(personal.forget(captured.item_id))
        active = personal.retrieve("concise")
        self.assertEqual(active.items, ())

    def test_confirm_inference_promotes_to_explicit(self) -> None:
        _, personal = self._manager()
        inferred = personal.capture(
            category="tool preference",
            value="local provider",
            source_type="interaction_pattern",
            source_reference="pattern-1",
            confidence=0.6,
            classification=PersonalClassification.INFERRED,
        )
        self.assertIsNotNone(inferred)
        confirmed = personal.confirm(inferred.item_id)
        self.assertIsNotNone(confirmed)
        self.assertEqual(confirmed.classification, PersonalClassification.EXPLICIT)

    def test_reject_inference_marks_disputed(self) -> None:
        _, personal = self._manager()
        inferred = personal.capture(
            category="tool preference",
            value="cloud only",
            source_type="interaction_pattern",
            source_reference="pattern-2",
            confidence=0.6,
            classification=PersonalClassification.INFERRED,
        )
        rejected = personal.reject(inferred.item_id)
        self.assertIsNotNone(rejected)
        explanation = personal.explain(inferred.item_id)
        self.assertEqual(explanation["classification"], PersonalClassification.DISPUTED)
        self.assertFalse(explanation["active"])

    def test_current_instruction_overrides_stored_preference(self) -> None:
        memory, personal = self._manager()
        personal.detect_candidates("I prefer concise answers.")
        conversation = ConversationManager(
            jarvis_core=JarvisCore(),
            memory_manager=memory,
            personal_intelligence_manager=personal,
        )
        conversation.jarvis_core.initialize()
        conversation.initialize()
        response = conversation.handle_input("Explain this in complete detail.")
        self.assertIn("personal_context_applied", response.execution_summary)
        self.assertFalse(response.execution_summary["personal_context_applied"])

    def test_conversation_manager_records_personal_context(self) -> None:
        memory, personal = self._manager()
        personal.detect_candidates("I prefer concise answers.")
        manager = ConversationManager(
            jarvis_core=JarvisCore(),
            memory_manager=memory,
            personal_intelligence_manager=personal,
        )
        manager.jarvis_core.initialize()
        manager.initialize()
        response = manager.handle_input("What do you know about my answer-length preference?")
        self.assertTrue(response.execution_summary["personal_context_applied"])

    def test_command_manager_profile_show(self) -> None:
        memory, personal = self._manager()
        personal.detect_candidates("I prefer concise answers.")
        manager = CommandManager()
        manager.initialize()
        session = ConversationSession()
        context = ConversationContext(session=session, metadata={"personal_intelligence_manager": personal})
        response = manager.execute("profile show", context)
        self.assertIn("communication preference", response.response)

    def test_command_manager_profile_explain(self) -> None:
        memory, personal = self._manager()
        captured = personal.detect_candidates("I prefer concise answers.")[0]
        manager = CommandManager()
        manager.initialize()
        context = ConversationContext(
            session=ConversationSession(),
            metadata={"personal_intelligence_manager": personal},
        )
        response = manager.execute(f"profile explain {captured.item_id}", context)
        self.assertIn("concise", response.response)

    def test_startup_and_health_include_personal_intelligence(self) -> None:
        startup = StartupManager()
        startup.start()
        try:
            self.assertIsNotNone(startup.personal_intelligence_manager)
            self.assertTrue(startup.personal_intelligence_manager.initialized)
            self.assertTrue(any(result.name == "personal_intelligence" for result in startup.health_results))
            checker = HealthChecker(
                settings=startup.settings,
                required_directories=startup.required_directories(startup.settings),
                module_checks={
                    "personal_intelligence": lambda: True,
                    "personal_memory": lambda: True,
                    "personal_retrieval": lambda: True,
                },
            )
            health = checker.check_module("personal_intelligence", "Personal Intelligence")
            self.assertEqual(health.message, "Personal Intelligence initialized.")
        finally:
            startup.shutdown()

    def test_relevant_personal_context_is_selective(self) -> None:
        _, personal = self._manager()
        personal.detect_candidates("I prefer concise answers.")
        personal.capture(
            category="tool preference",
            value="local provider",
            source_type="direct_user_statement",
            source_reference="conversation-3",
            confidence=0.9,
            classification=PersonalClassification.EXPLICIT,
        )
        selected = personal.search("answer length")
        self.assertTrue(any(item.category == "communication preference" for item in selected))
        self.assertFalse(any(item.category == "tool preference" and "answer" in item.value for item in selected))

    def test_missing_information_returns_empty_result(self) -> None:
        _, personal = self._manager()
        self.assertEqual(personal.retrieve("unknown topic").items, ())

    def test_durable_memory_is_authoritative(self) -> None:
        memory, personal = self._manager()
        captured = personal.detect_candidates("I prefer concise answers.")[0]
        memory_item = memory.get_memory(captured.memory_id)
        self.assertIsNotNone(memory_item)
        self.assertIn("personal_intelligence", memory_item.metadata)


if __name__ == "__main__":
    unittest.main()
