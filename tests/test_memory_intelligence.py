"""Tests for the higher-level local memory intelligence layer."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from conversation import ConversationManager
from memory import MemoryIntelligenceManager, MemoryManager


class MemoryIntelligenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.memory_manager = MemoryManager(Path(self.tempdir.name))
        self.memory_manager.initialize()
        self.memory_intelligence = MemoryIntelligenceManager(
            self.memory_manager,
            auto_remember=True,
            auto_session_summary=True,
        )
        self.memory_intelligence.initialize()

    def test_status_and_preferences_are_safe(self) -> None:
        status = self.memory_intelligence.status()
        self.assertTrue(status.enabled)
        self.assertTrue(status.local_only)
        self.assertTrue(status.auto_session_summary)
        self.assertIn("enabled=yes", self.memory_intelligence.status_text())
        preferences = self.memory_intelligence.preferences()
        self.assertFalse(preferences.auto_remember is False and preferences.auto_session_summary is False)

    def test_remember_search_show_update_and_forget(self) -> None:
        created = self.memory_intelligence.remember(
            "Coffee preference",
            "I prefer decaf after 6 PM.",
            tags=("preference", "coffee"),
            project="JarvisOS",
            user_confirmed=True,
        )
        self.assertIsNotNone(created)
        assert created is not None
        results = self.memory_intelligence.search("decaf")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].memory.id, created.id)
        snapshot = self.memory_intelligence.get(created.id)
        self.assertIsNotNone(snapshot)
        self.assertIn("decaf", snapshot.content)
        updated = self.memory_intelligence.update(created.id, content="I prefer black tea after 6 PM.")
        self.assertIsNotNone(updated)
        self.assertIn("tea", self.memory_intelligence.get(created.id).content)  # type: ignore[union-attr]
        self.assertTrue(self.memory_intelligence.forget(created.id))
        self.assertIsNone(self.memory_intelligence.get(created.id))

    def test_secret_like_content_is_blocked(self) -> None:
        created = self.memory_intelligence.remember(
            "Secret note",
            "api key = sk-1234567890abcdef",
            user_confirmed=True,
        )
        self.assertIsNone(created)

    def test_auto_remember_turn_creates_context_memory(self) -> None:
        created = self.memory_intelligence.auto_remember_turn(
            "Remember I like oatmeal.",
            "Got it, you like oatmeal.",
            conversation_id="conversation-1",
        )
        self.assertIsNotNone(created)
        self.assertGreaterEqual(self.memory_manager.count_memories(), 1)

    def test_cleanup_and_audit_are_bounded(self) -> None:
        first = self.memory_intelligence.remember("A", "Shared detail", user_confirmed=True)
        second = self.memory_intelligence.remember("B", "Shared detail", user_confirmed=True)
        self.assertIsNotNone(first)
        self.assertIsNotNone(second)
        result = self.memory_intelligence.cleanup()
        self.assertGreaterEqual(result.considered, 2)
        self.assertGreaterEqual(result.updated, 1)
        events = self.memory_intelligence.audit()
        self.assertTrue(events)
        self.assertLessEqual(len(events), 20)

    def test_conversation_manager_receives_memory_commands(self) -> None:
        core = None
        manager = ConversationManager(
            jarvis_core=core,
            memory_manager=self.memory_manager,
            memory_intelligence_manager=self.memory_intelligence,
        )
        manager.initialize()
        response = manager.handle_input("memory status")
        self.assertIn("enabled=yes", response.response)
        response = manager.handle_input("memory help")
        self.assertIn("memory commands", response.response)


if __name__ == "__main__":
    unittest.main()
