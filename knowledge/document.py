"""Knowledge document models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4


class DocumentType(StrEnum):
    """Supported local document types."""

    MARKDOWN = "markdown"
    TXT = "txt"
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    JSON = "json"
    CSV = "csv"
    PYTHON = "python"
    UNKNOWN = "unknown"


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


def datetime_to_text(value: datetime) -> str:
    """Serialize a datetime for SQLite storage."""
    return value.astimezone(timezone.utc).isoformat()


def datetime_from_text(value: str) -> datetime:
    """Deserialize a datetime from SQLite storage."""
    return datetime.fromisoformat(value)


@dataclass(frozen=True, slots=True)
class KnowledgeDocument:
    """Structured document imported into the Knowledge Engine."""

    document_id: str
    title: str
    path: Path
    document_type: DocumentType
    created_at: datetime
    modified_at: datetime
    author: str | None = None
    language: str = "en"
    tags: tuple[str, ...] = ()
    related_tasks: tuple[str, ...] = ()
    related_memories: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class KnowledgeChunk:
    """Searchable chunk extracted from a document."""

    chunk_id: str
    document_id: str
    content: str
    sequence: int
    source_location: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """Reader output before storage."""

    title: str
    path: Path
    document_type: DocumentType
    content: str
    created_at: datetime
    modified_at: datetime
    author: str | None = None
    language: str = "en"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class KnowledgeImportResult:
    """Result returned after importing a document."""

    document: KnowledgeDocument
    chunks: tuple[KnowledgeChunk, ...]
    linked_memory_id: str | None = None


@dataclass(frozen=True, slots=True)
class KnowledgeStatistics:
    """Operational Knowledge Engine statistics."""

    total_documents: int
    total_chunks: int
    database_size_bytes: int
    database_path: Path


def new_document_id() -> str:
    """Return a new document UUID string."""
    return str(uuid4())


def new_chunk_id() -> str:
    """Return a new chunk UUID string."""
    return str(uuid4())

