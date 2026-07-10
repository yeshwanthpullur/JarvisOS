"""Research note support for the Obsidian Brain layer."""

from __future__ import annotations

from brain.note_manager import BrainNote, NoteManager


class ResearchNoteManager:
    """Creates research notes without AI summarization."""

    def __init__(self, note_manager: NoteManager) -> None:
        self._notes = note_manager

    def create_research_note(
        self,
        title: str,
        question: str,
        sources: tuple[str, ...] = (),
    ) -> BrainNote:
        """Create a research note shell."""
        body = (
            f"## Question\n{question}\n\n"
            "## Sources\n"
            + self._bullet_list(sources)
            + "\n## Findings\n\n## Open Questions\n"
        )
        return self._notes.create_note(
            title=title,
            body=body,
            folder="Research",
            note_type="research",
            tags=("research",),
            metadata={"sources": sources},
        )

    def _bullet_list(self, values: tuple[str, ...]) -> str:
        if not values:
            return "\n"
        return "".join(f"- {value}\n" for value in values)
