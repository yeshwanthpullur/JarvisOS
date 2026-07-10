"""Future summarization interfaces for the Knowledge Engine."""

from __future__ import annotations

from abc import ABC, abstractmethod

from knowledge.document import KnowledgeDocument, KnowledgeChunk


class KnowledgeSummarizer(ABC):
    """Interface for future AI or non-AI summarizers."""

    @abstractmethod
    def summarize(
        self,
        document: KnowledgeDocument,
        chunks: tuple[KnowledgeChunk, ...],
    ) -> str:
        """Summarize a document in a future implementation."""


class NoOpSummarizer(KnowledgeSummarizer):
    """Summarizer placeholder that intentionally performs no summarization."""

    def summarize(
        self,
        document: KnowledgeDocument,
        chunks: tuple[KnowledgeChunk, ...],
    ) -> str:
        """Raise because summarization is not implemented yet."""
        raise NotImplementedError("Knowledge summarization is not implemented yet.")

