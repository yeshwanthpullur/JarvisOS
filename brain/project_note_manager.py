"""Project note support for the Obsidian Brain layer."""

from __future__ import annotations

from brain.note_manager import BrainNote, NoteManager


class ProjectNoteManager:
    """Creates human-readable project notes."""

    def __init__(self, note_manager: NoteManager) -> None:
        self._notes = note_manager

    def create_project_note(
        self,
        title: str,
        description: str = "",
        project_id: str | None = None,
        related_tasks: tuple[str, ...] = (),
        related_memories: tuple[str, ...] = (),
        related_knowledge: tuple[str, ...] = (),
        related_documents: tuple[str, ...] = (),
        related_ideas: tuple[str, ...] = (),
    ) -> BrainNote:
        """Create a project note with standard tracking sections."""
        body = (
            f"{description.strip()}\n\n"
            "## Goals\n\n"
            "## Progress\n\n"
            f"## Related Tasks\n{self._bullet_list(related_tasks)}\n"
            f"## Related Memories\n{self._bullet_list(related_memories)}\n"
            f"## Related Knowledge\n{self._bullet_list(related_knowledge)}\n"
            f"## Related Documents\n{self._bullet_list(related_documents)}\n"
            f"## Related Ideas\n{self._bullet_list(related_ideas)}"
        )
        return self._notes.create_note(
            title=title,
            body=body,
            folder="Projects",
            note_type="project",
            tags=("project",),
            project_id=project_id,
            metadata={
                "related_tasks": related_tasks,
                "related_memories": related_memories,
                "related_knowledge": related_knowledge,
                "related_documents": related_documents,
                "related_ideas": related_ideas,
            },
        )

    def _bullet_list(self, values: tuple[str, ...]) -> str:
        if not values:
            return "\n"
        return "".join(f"- {value}\n" for value in values)
