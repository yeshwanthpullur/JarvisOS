"""Knowledge note support for imported documents."""

from __future__ import annotations

from brain.note_manager import BrainNote, NoteManager
from knowledge import KnowledgeDocument


class KnowledgeNoteManager:
    """Creates Markdown notes for Knowledge Engine documents."""

    def __init__(self, note_manager: NoteManager) -> None:
        self._notes = note_manager

    def create_for_document(self, document: KnowledgeDocument) -> BrainNote:
        """Create a knowledge note linked to a Knowledge Engine document."""
        body = (
            f"Source path: `{document.path}`\n\n"
            f"Document type: `{document.document_type.value}`\n\n"
            "## Related Memories\n"
            + self._bullet_list(document.related_memories)
        )
        return self._notes.create_note(
            title=document.title,
            body=body,
            folder="Knowledge",
            note_type="knowledge",
            tags=("knowledge", *document.tags),
            knowledge_id=document.document_id,
            related_notes=(),
            metadata={
                "source_path": str(document.path),
                "document_type": document.document_type.value,
                "related_tasks": document.related_tasks,
                "related_memories": document.related_memories,
            },
        )

    def _bullet_list(self, values: tuple[str, ...]) -> str:
        if not values:
            return "\n"
        return "".join(f"- {value}\n" for value in values)
