"""Relationship building hooks for imported knowledge."""

from __future__ import annotations

import logging

from knowledge.document import KnowledgeDocument
from knowledge.knowledge_store import KnowledgeStore


class RelationshipBuilder:
    """Builds explicit relationships between documents and other systems."""

    def __init__(
        self,
        store: KnowledgeStore,
        logger: logging.Logger | None = None,
    ) -> None:
        self._store = store
        self._logger = logger or logging.getLogger(__name__)

    def link_document_to_memory(
        self,
        document: KnowledgeDocument,
        memory_id: str,
    ) -> None:
        """Link an imported document to a Memory Engine record."""
        self._store.link_memory(document.document_id, memory_id)
        self._logger.info(
            "knowledge_document_memory_linked document_id=%s memory_id=%s",
            document.document_id,
            memory_id,
        )

