"""Skill note support for the Obsidian Brain layer."""

from __future__ import annotations

from brain.note_manager import BrainNote, NoteManager


class SkillNoteManager:
    """Creates human-readable skill memory notes."""

    def __init__(self, note_manager: NoteManager) -> None:
        self._notes = note_manager

    def create_skill_note(
        self,
        title: str,
        procedure: str,
        tags: tuple[str, ...] = (),
    ) -> BrainNote:
        """Create a skill note."""
        body = f"## Procedure\n{procedure}\n\n## Preconditions\n\n## Safety Notes\n"
        return self._notes.create_note(
            title=title,
            body=body,
            folder="Skills",
            note_type="skill",
            tags=("skill", *tags),
        )
