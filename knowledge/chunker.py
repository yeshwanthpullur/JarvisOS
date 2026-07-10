"""Document chunking for searchable knowledge."""

from __future__ import annotations

from knowledge.document import KnowledgeChunk, new_chunk_id


class KnowledgeChunker:
    """Splits document content into searchable chunks."""

    def __init__(self, max_characters: int = 1200) -> None:
        self._max_characters = max_characters

    def chunk(self, document_id: str, content: str) -> tuple[KnowledgeChunk, ...]:
        """Create chunks from document content."""
        paragraphs = [part.strip() for part in content.splitlines() if part.strip()]
        if not paragraphs and content.strip():
            paragraphs = [content.strip()]

        chunks: list[KnowledgeChunk] = []
        current: list[str] = []
        current_length = 0

        for paragraph in paragraphs:
            if current and current_length + len(paragraph) + 1 > self._max_characters:
                chunks.append(self._build_chunk(document_id, len(chunks), current))
                current = []
                current_length = 0

            current.append(paragraph)
            current_length += len(paragraph) + 1

        if current:
            chunks.append(self._build_chunk(document_id, len(chunks), current))

        return tuple(chunks)

    def _build_chunk(
        self,
        document_id: str,
        sequence: int,
        parts: list[str],
    ) -> KnowledgeChunk:
        return KnowledgeChunk(
            chunk_id=new_chunk_id(),
            document_id=document_id,
            content="\n".join(parts),
            sequence=sequence,
            source_location=f"chunk:{sequence}",
        )

