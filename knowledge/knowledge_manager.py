"""Public facade for the JARVIS OS Knowledge Engine."""

from __future__ import annotations

import logging
from pathlib import Path

from knowledge.chunker import KnowledgeChunker
from knowledge.document import (
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeImportResult,
    KnowledgeStatistics,
    new_document_id,
)
from knowledge.knowledge_store import KnowledgeStore
from knowledge.reader import KnowledgeReader
from knowledge.relationship_builder import RelationshipBuilder
from memory import MemoryManager


class KnowledgeManager:
    """Coordinates reading, parsing, chunking, storage, and memory linking."""

    def __init__(
        self,
        storage_dir: Path,
        memory_manager: MemoryManager | None = None,
        database_name: str = "jarvis_knowledge.db",
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._store = KnowledgeStore(storage_dir / database_name)
        self._reader = KnowledgeReader(logger=self._logger)
        self._chunker = KnowledgeChunker()
        self._relationships = RelationshipBuilder(self._store, logger=self._logger)
        self._memory_manager = memory_manager
        self.initialized = False

    @property
    def database_path(self) -> Path:
        """Return the Knowledge Engine database path."""
        return self._store.database_path

    def initialize(self) -> None:
        """Initialize and verify the Knowledge Engine store."""
        self._store.initialize()
        if not self._store.verify_schema():
            raise RuntimeError("Knowledge database schema verification failed.")
        self.initialized = True
        self._logger.info("knowledge_engine_initialized path=%s", self.database_path)

    def verify_schema(self) -> bool:
        """Return whether the Knowledge Engine schema is ready."""
        return self._store.verify_schema()

    def import_file(
        self,
        path: Path,
        tags: tuple[str, ...] = (),
        related_tasks: tuple[str, ...] = (),
        related_memories: tuple[str, ...] = (),
    ) -> KnowledgeImportResult:
        """Import a local file into structured, searchable knowledge."""
        self._ensure_initialized()
        parsed = self._reader.read_file(path)
        document_id = new_document_id()
        chunks = self._chunker.chunk(document_id, parsed.content)
        linked_memory_id = self._create_memory_for_document(
            title=parsed.title,
            content=parsed.content,
            tags=tags,
            related_tasks=related_tasks,
            related_memories=related_memories,
        )
        memory_links = (
            (*related_memories, linked_memory_id)
            if linked_memory_id is not None
            else related_memories
        )
        document = KnowledgeDocument(
            document_id=document_id,
            title=parsed.title,
            path=parsed.path,
            document_type=parsed.document_type,
            created_at=parsed.created_at,
            modified_at=parsed.modified_at,
            author=parsed.author,
            language=parsed.language,
            tags=tags,
            related_tasks=related_tasks,
            related_memories=memory_links,
            metadata=parsed.metadata,
        )
        self._store.save_document(document, chunks)
        if linked_memory_id is not None:
            self._relationships.link_document_to_memory(document, linked_memory_id)

        self._logger.info(
            "knowledge_document_imported document_id=%s path=%s chunks=%s",
            document.document_id,
            document.path,
            len(chunks),
        )
        return KnowledgeImportResult(
            document=document,
            chunks=chunks,
            linked_memory_id=linked_memory_id,
        )

    def search_knowledge(self, query: str, limit: int = 20) -> tuple[KnowledgeChunk, ...]:
        """Search imported knowledge chunks."""
        self._ensure_initialized()
        results = self._store.search_chunks(query, limit=limit)
        self._logger.info("knowledge_search query=%s count=%s", query, len(results))
        return results

    def get_document(self, document_id: str) -> KnowledgeDocument | None:
        """Return a stored knowledge document."""
        self._ensure_initialized()
        return self._store.get_document(document_id)

    def list_documents(self, limit: int = 100) -> tuple[KnowledgeDocument, ...]:
        """List stored knowledge documents."""
        self._ensure_initialized()
        return self._store.list_documents(limit=limit)

    def statistics(self) -> KnowledgeStatistics:
        """Return Knowledge Engine statistics."""
        self._ensure_initialized()
        return self._store.statistics()

    def _create_memory_for_document(
        self,
        title: str,
        content: str,
        tags: tuple[str, ...],
        related_tasks: tuple[str, ...],
        related_memories: tuple[str, ...],
    ) -> str | None:
        if self._memory_manager is None or not self._memory_manager.initialized:
            return None

        preview = content[:4000]
        memory = self._memory_manager.create_memory(
            title=f"Document: {title}",
            content=preview,
            source="knowledge_import",
            importance=1,
            tags=("knowledge", *tags),
            metadata={
                "related_tasks": related_tasks,
                "related_memories": related_memories,
            },
        )
        return memory.id

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("KnowledgeManager must be initialized before use.")

