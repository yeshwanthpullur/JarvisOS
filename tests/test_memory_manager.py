"""Tests for the SQLite memory engine."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from memory import MemoryManager


class MemoryManagerTests(unittest.TestCase):
    """MemoryManager integration tests using a temporary SQLite database."""

    def test_initialize_creates_required_tables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manager = MemoryManager(Path(directory))
            manager.initialize()

            self.assertTrue(manager.database_path.exists())
            self.assertTrue(manager.verify_schema())

            connection = sqlite3.connect(manager.database_path)
            try:
                tables = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type = 'table'"
                    )
                }
            finally:
                connection.close()

        self.assertIn("memories", tables)
        self.assertIn("sessions", tables)
        self.assertIn("projects", tables)
        self.assertIn("tags", tables)
        self.assertIn("relationships", tables)

    def test_create_get_update_search_list_count_and_delete_memory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manager = MemoryManager(Path(directory))
            manager.initialize()

            created = manager.create_memory(
                title="Architecture decision",
                content="Use SQLite for structured local memory.",
                source="unit-test",
                importance=3,
                tags=("architecture", "memory"),
                project="JarvisOS",
                session_id="test-session",
                metadata={"decision": True},
            )

            self.assertEqual(manager.count_memories(), 1)
            self.assertEqual(manager.statistics().total_sessions, 1)

            fetched = manager.get_memory(created.id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.title, "Architecture decision")
            self.assertEqual(fetched.project, "JarvisOS")
            self.assertEqual(fetched.tags, ("architecture", "memory"))

            updated = manager.update_memory(
                created.id,
                title="Updated architecture decision",
                tags=("memory",),
                metadata={"decision": True, "updated": True},
            )
            self.assertIsNotNone(updated)
            self.assertEqual(updated.title, "Updated architecture decision")
            self.assertEqual(updated.tags, ("memory",))

            results = manager.search_memory("SQLite", tags=("memory",))
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].id, created.id)

            listed = manager.list_memories()
            self.assertEqual(len(listed), 1)

            self.assertTrue(manager.delete_memory(created.id))
            self.assertEqual(manager.count_memories(), 0)
            self.assertIsNone(manager.get_memory(created.id))


if __name__ == "__main__":
    unittest.main()
