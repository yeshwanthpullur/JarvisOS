"""Conversation note support for the Obsidian Brain layer."""

from __future__ import annotations

from brain.note_manager import BrainNote, NoteManager


class ConversationNoteManager:
    """Creates readable conversation notes."""

    def __init__(self, note_manager: NoteManager) -> None:
        self._notes = note_manager

    def create_conversation_note(
        self,
        title: str,
        transcript: str,
        session_id: str | None = None,
    ) -> BrainNote:
        """Create a conversation note."""
        return self._notes.create_note(
            title=title,
            body=transcript,
            folder="Conversations",
            note_type="conversation",
            tags=("conversation",),
            metadata={"session_id": session_id},
        )
