"""Daily note support for the Obsidian Brain layer."""

from __future__ import annotations

from datetime import datetime

from brain.note_manager import BrainNote, NoteManager


class DailyNoteManager:
    """Creates and appends structured entries to daily notes."""

    def __init__(self, note_manager: NoteManager, date_format: str = "%Y-%m-%d") -> None:
        self._notes = note_manager
        self._date_format = date_format

    def create_today(self) -> BrainNote:
        """Create today's daily note if needed and return it."""
        title = datetime.now().strftime(self._date_format)
        body = (
            "## Tasks Completed\n\n"
            "## Knowledge Imported\n\n"
            "## Memories Created\n\n"
            "## Ideas\n\n"
            "## Errors\n\n"
            "## Research Completed\n\n"
            "## System Summaries\n"
        )
        try:
            return self._notes.create_note(
                title=title,
                body=body,
                folder="Daily Notes",
                note_type="daily",
                tags=("daily",),
            )
        except FileExistsError:
            return self._notes.read_note(self._notes.note_path("Daily Notes", title))

    def record(self, section: str, entry: str) -> BrainNote:
        """Append an entry under a named daily note section."""
        note = self.create_today()
        marker = f"## {section}"
        body = note.content
        if marker not in body:
            body = body.rstrip() + f"\n\n{marker}\n"
        body = body.rstrip() + f"\n- {entry}\n"
        return self._notes.update_note(note.path, body=body)
