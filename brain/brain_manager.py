"""Top-level Brain manager for human-readable Markdown knowledge."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from brain.conversation_note_manager import ConversationNoteManager
from brain.daily_note_manager import DailyNoteManager
from brain.knowledge_note_manager import KnowledgeNoteManager
from brain.note_manager import BrainNote
from brain.obsidian_manager import ObsidianManager
from brain.project_note_manager import ProjectNoteManager
from brain.research_note_manager import ResearchNoteManager
from brain.skill_note_manager import SkillNoteManager
from brain.vault_manager import VaultStatus
from knowledge import KnowledgeDocument
from memory import Memory
from tasks import Task


@dataclass(frozen=True, slots=True)
class BrainStatistics:
    """Operational statistics for the Brain layer."""

    vault_name: str
    vault_path: Path
    total_notes: int
    connected: bool


class BrainManager:
    """Coordinates the Obsidian Brain layer and core engine integrations."""

    def __init__(
        self,
        vault_path: Path,
        vault_name: str,
        auto_create_vault: bool = False,
        daily_note_format: str = "%Y-%m-%d",
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._auto_create_vault = auto_create_vault
        self.obsidian = ObsidianManager(vault_path, vault_name, logger=self._logger)
        self.daily_notes = DailyNoteManager(
            self.obsidian.notes,
            date_format=daily_note_format,
        )
        self.project_notes = ProjectNoteManager(self.obsidian.notes)
        self.knowledge_notes = KnowledgeNoteManager(self.obsidian.notes)
        self.research_notes = ResearchNoteManager(self.obsidian.notes)
        self.skill_notes = SkillNoteManager(self.obsidian.notes)
        self.conversation_notes = ConversationNoteManager(self.obsidian.notes)
        self.initialized = False
        self._last_status: VaultStatus | None = None

    @property
    def vault_path(self) -> Path:
        """Return the configured vault path."""
        return self.obsidian.vault.vault_path

    def initialize(self) -> BrainStatistics:
        """Connect to the Obsidian vault and prepare today's daily note."""
        self._last_status = self.obsidian.initialize(
            create_if_missing=self._auto_create_vault
        )
        self.initialized = self._last_status.connected
        if self.initialized:
            self.daily_notes.create_today()
            self._logger.info("brain_manager_initialized path=%s", self.vault_path)
        else:
            self._logger.warning("brain_manager_not_connected path=%s", self.vault_path)
        return self.statistics()

    def verify_connection(self) -> bool:
        """Return whether the Brain layer is connected to a vault."""
        return self.initialized and self.vault_path.exists()

    def statistics(self) -> BrainStatistics:
        """Return Brain layer statistics."""
        status = self.obsidian.vault.status()
        return BrainStatistics(
            vault_name=status.vault_name,
            vault_path=status.vault_path,
            total_notes=status.total_notes,
            connected=status.connected,
        )

    def create_memory_note(self, memory: Memory) -> BrainNote:
        """Create a human-readable note linked to a Memory Engine record."""
        note = self.obsidian.notes.create_note(
            title=memory.title,
            body=memory.content,
            folder="Knowledge",
            note_type="memory",
            tags=("memory", *memory.tags),
            importance=memory.importance,
            source=memory.source,
            project_id=memory.project,
            memory_id=memory.id,
            metadata=memory.metadata,
        )
        self.obsidian.graph.add_relationship(memory.id, str(note.path), "memory_note")
        self.daily_notes.record("Memories Created", f"{memory.title} ({memory.id})")
        return note

    def create_knowledge_note(self, document: KnowledgeDocument) -> BrainNote:
        """Create a human-readable note linked to a Knowledge Engine document."""
        note = self.knowledge_notes.create_for_document(document)
        self.obsidian.graph.add_relationship(
            document.document_id,
            str(note.path),
            "knowledge_note",
        )
        self.daily_notes.record(
            "Knowledge Imported",
            f"{document.title} ({document.document_id})",
        )
        return note

    def create_task_note(self, task: Task) -> BrainNote:
        """Create a human-readable note linked to a Task Engine task."""
        body = (
            f"Description: {task.description}\n\n"
            f"Status: `{task.status.value}`\n\n"
            f"Priority: `{task.priority.name.lower()}`\n\n"
            "## Logs\n"
            + "".join(f"- {entry.timestamp.isoformat()} {entry.message}\n" for entry in task.logs)
        )
        note = self.obsidian.notes.create_note(
            title=task.name,
            body=body,
            folder="Tasks",
            note_type="task",
            tags=("task",),
            task_id=task.task_id,
            metadata={
                "assigned_agent": task.assigned_agent,
                "related_memories": task.related_memories,
                "dependencies": task.dependencies,
            },
        )
        self.obsidian.graph.add_relationship(task.task_id, str(note.path), "task_note")
        return note
