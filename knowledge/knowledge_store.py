"""SQLite store for documents and searchable knowledge chunks."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from knowledge.document import (
    DocumentType,
    KnowledgeChunk,
    KnowledgeDocument,
    KnowledgeStatistics,
    datetime_from_text,
    datetime_to_text,
)


class KnowledgeStore:
    """Persists imported documents, chunks, and memory links."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def connect(self) -> sqlite3.Connection:
        """Create a configured SQLite connection."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def session(self) -> Iterator[sqlite3.Connection]:
        """Yield a SQLite connection and always close it."""
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create the knowledge schema."""
        with self.session() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS knowledge_documents (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    path TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL,
                    author TEXT,
                    language TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',
                    related_tasks TEXT NOT NULL DEFAULT '[]',
                    related_memories TEXT NOT NULL DEFAULT '[]',
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS knowledge_chunks (
                    id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    source_location TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY (document_id) REFERENCES knowledge_documents(id)
                        ON UPDATE CASCADE ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS knowledge_memory_links (
                    document_id TEXT NOT NULL,
                    memory_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    PRIMARY KEY (document_id, memory_id, relationship_type),
                    FOREIGN KEY (document_id) REFERENCES knowledge_documents(id)
                        ON UPDATE CASCADE ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_knowledge_documents_type
                    ON knowledge_documents(document_type);
                CREATE INDEX IF NOT EXISTS idx_knowledge_documents_path
                    ON knowledge_documents(path);
                CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_document
                    ON knowledge_chunks(document_id);
                CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_sequence
                    ON knowledge_chunks(document_id, sequence);
                """
            )

    def verify_schema(self) -> bool:
        """Return whether required knowledge tables exist."""
        with self.session() as connection:
            tables = {
                row["name"]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        return {
            "knowledge_documents",
            "knowledge_chunks",
            "knowledge_memory_links",
        }.issubset(tables)

    def save_document(
        self,
        document: KnowledgeDocument,
        chunks: tuple[KnowledgeChunk, ...],
    ) -> None:
        """Persist a document and its chunks."""
        with self.session() as connection:
            connection.execute(
                """
                INSERT OR REPLACE INTO knowledge_documents (
                    id, title, path, document_type, created_at, modified_at,
                    author, language, tags, related_tasks, related_memories, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document.document_id,
                    document.title,
                    str(document.path),
                    document.document_type.value,
                    datetime_to_text(document.created_at),
                    datetime_to_text(document.modified_at),
                    document.author,
                    document.language,
                    json.dumps(document.tags),
                    json.dumps(document.related_tasks),
                    json.dumps(document.related_memories),
                    json.dumps(document.metadata, sort_keys=True),
                ),
            )
            connection.execute(
                "DELETE FROM knowledge_chunks WHERE document_id = ?",
                (document.document_id,),
            )
            connection.executemany(
                """
                INSERT INTO knowledge_chunks (
                    id, document_id, content, sequence, source_location, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        chunk.chunk_id,
                        chunk.document_id,
                        chunk.content,
                        chunk.sequence,
                        chunk.source_location,
                        json.dumps(chunk.metadata, sort_keys=True),
                    )
                    for chunk in chunks
                ],
            )

    def link_memory(
        self,
        document_id: str,
        memory_id: str,
        relationship_type: str = "imported_as_memory",
    ) -> None:
        """Link a document to a memory record."""
        with self.session() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO knowledge_memory_links (
                    document_id, memory_id, relationship_type
                )
                VALUES (?, ?, ?)
                """,
                (document_id, memory_id, relationship_type),
            )

    def search_chunks(self, query: str, limit: int = 20) -> tuple[KnowledgeChunk, ...]:
        """Search chunks by plain text."""
        pattern = f"%{query.strip()}%"
        with self.session() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM knowledge_chunks
                WHERE content LIKE ?
                ORDER BY document_id ASC, sequence ASC
                LIMIT ?
                """,
                (pattern, limit),
            ).fetchall()
        return tuple(self._row_to_chunk(row) for row in rows)

    def get_document(self, document_id: str) -> KnowledgeDocument | None:
        """Return a stored document by ID."""
        with self.session() as connection:
            row = connection.execute(
                "SELECT * FROM knowledge_documents WHERE id = ?",
                (document_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_document(row)

    def list_documents(self, limit: int = 100) -> tuple[KnowledgeDocument, ...]:
        """List stored documents."""
        with self.session() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM knowledge_documents
                ORDER BY modified_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return tuple(self._row_to_document(row) for row in rows)

    def statistics(self) -> KnowledgeStatistics:
        """Return Knowledge Engine statistics."""
        with self.session() as connection:
            total_documents = int(
                connection.execute("SELECT COUNT(*) FROM knowledge_documents").fetchone()[0]
            )
            total_chunks = int(
                connection.execute("SELECT COUNT(*) FROM knowledge_chunks").fetchone()[0]
            )
        return KnowledgeStatistics(
            total_documents=total_documents,
            total_chunks=total_chunks,
            database_size_bytes=self.size_bytes(),
            database_path=self.database_path,
        )

    def size_bytes(self) -> int:
        """Return database file size in bytes."""
        if not self.database_path.exists():
            return 0
        return self.database_path.stat().st_size

    def _row_to_document(self, row: sqlite3.Row) -> KnowledgeDocument:
        return KnowledgeDocument(
            document_id=str(row["id"]),
            title=str(row["title"]),
            path=Path(str(row["path"])),
            document_type=DocumentType(str(row["document_type"])),
            created_at=datetime_from_text(str(row["created_at"])),
            modified_at=datetime_from_text(str(row["modified_at"])),
            author=row["author"],
            language=str(row["language"]),
            tags=tuple(json.loads(str(row["tags"]))),
            related_tasks=tuple(json.loads(str(row["related_tasks"]))),
            related_memories=tuple(json.loads(str(row["related_memories"]))),
            metadata=json.loads(str(row["metadata"])),
        )

    def _row_to_chunk(self, row: sqlite3.Row) -> KnowledgeChunk:
        return KnowledgeChunk(
            chunk_id=str(row["id"]),
            document_id=str(row["document_id"]),
            content=str(row["content"]),
            sequence=int(row["sequence"]),
            source_location=str(row["source_location"]),
            metadata=json.loads(str(row["metadata"])),
        )

