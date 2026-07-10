"""Tests for the Obsidian Brain integration."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from brain import BrainManager, FrontmatterManager, REQUIRED_VAULT_FOLDERS, VaultManager
from knowledge import DocumentType, KnowledgeDocument
from knowledge.document import utc_now
from memory import MemoryManager
from tasks import TaskManager


class ObsidianBrainTests(unittest.TestCase):
    """Vault, note, search, frontmatter, backlink, and integration tests."""

    def test_vault_creation_and_required_folders(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "vault"
            manager = VaultManager(vault, "Test Vault")

            status = manager.connect(create_if_missing=True)

            self.assertTrue(status.connected)
            for folder in REQUIRED_VAULT_FOLDERS:
                self.assertTrue((vault / folder).is_dir())

    def test_note_creation_update_search_frontmatter_and_backlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            brain = BrainManager(
                Path(directory) / "vault",
                "Test Vault",
                auto_create_vault=True,
            )
            brain.initialize()

            note = brain.obsidian.notes.create_note(
                title="Architecture Decision",
                body="Link to [[Related Note]] for context.",
                folder="Decisions",
                note_type="decision",
                tags=("architecture",),
                metadata={"layer": "brain"},
            )
            updated = brain.obsidian.notes.update_note(
                note.path,
                body="Updated content with [[Related Note]].",
                frontmatter_updates={"status": "reviewed"},
            )
            related = brain.obsidian.notes.create_note(
                title="Related Note",
                body="Backlink target.",
                folder="Ideas",
                note_type="idea",
            )

            results = brain.obsidian.notes.search_notes("architecture")
            backlinks = brain.obsidian.notes.read_backlinks("Related Note")
            frontmatter = brain.obsidian.notes.read_frontmatter(updated.path)

            self.assertEqual(updated.frontmatter["status"], "reviewed")
            self.assertEqual(frontmatter["metadata"]["layer"], "brain")
            self.assertTrue(results)
            self.assertIn(note.path, backlinks)
            self.assertEqual(
                brain.obsidian.notes.resolve_wiki_link("Related Note"),
                related.path,
            )

    def test_frontmatter_round_trip(self) -> None:
        manager = FrontmatterManager()
        frontmatter = manager.create(
            title="Memory Note",
            note_type="memory",
            tags=("memory", "test"),
            memory_id="memory-1",
            metadata={"safe": True},
        )

        raw = manager.render(frontmatter)
        parsed, body = manager.split(raw + "Body")

        self.assertEqual(parsed["title"], "Memory Note")
        self.assertEqual(parsed["tags"], ["memory", "test"])
        self.assertEqual(parsed["memory_id"], "memory-1")
        self.assertEqual(parsed["metadata"], {"safe": True})
        self.assertEqual(body, "Body")

    def test_memory_knowledge_and_task_note_integrations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            brain = BrainManager(root / "vault", "Test Vault", auto_create_vault=True)
            brain.initialize()

            memory_manager = MemoryManager(root / "memory")
            memory_manager.initialize()
            memory = memory_manager.create_memory(
                title="SQLite Memory",
                content="Structured memory remains in SQLite.",
                tags=("memory",),
            )
            memory_note = brain.create_memory_note(memory)

            document = KnowledgeDocument(
                document_id="knowledge-1",
                title="Knowledge Source",
                path=root / "source.md",
                document_type=DocumentType.MARKDOWN,
                created_at=utc_now(),
                modified_at=utc_now(),
                tags=("docs",),
                related_memories=(memory.id,),
            )
            knowledge_note = brain.create_knowledge_note(document)

            task_manager = TaskManager()
            task_manager.initialize()
            task = task_manager.create_task("Brain Task", "Create readable task note.")
            task_note = brain.create_task_note(task)

            self.assertEqual(memory_note.frontmatter["memory_id"], memory.id)
            self.assertEqual(knowledge_note.frontmatter["knowledge_id"], "knowledge-1")
            self.assertEqual(task_note.frontmatter["task_id"], task.task_id)
            self.assertGreaterEqual(brain.statistics().total_notes, 4)

    def test_templates_and_markdown_generation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            brain = BrainManager(
                Path(directory) / "vault",
                "Test Vault",
                auto_create_vault=True,
            )
            brain.initialize()
            brain.obsidian.templates.save_template("project", "Project: $name")

            rendered = brain.obsidian.templates.render_template(
                "project",
                {"name": "Jarvis"},
            )

            self.assertEqual(rendered, "Project: Jarvis")


if __name__ == "__main__":
    unittest.main()
