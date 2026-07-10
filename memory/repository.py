"""SQLite repository for structured memory records."""

from __future__ import annotations

import json
import logging
import sqlite3
from uuid import uuid4

from memory.database import MemoryDatabase
from memory.models import (
    Memory,
    MemoryCreate,
    MemoryStatistics,
    MemoryUpdate,
    datetime_from_text,
    datetime_to_text,
    utc_now,
)


class MemoryRepository:
    """Persists and retrieves memory records using SQLite."""

    def __init__(
        self,
        database: MemoryDatabase,
        logger: logging.Logger | None = None,
    ) -> None:
        self._database = database
        self._logger = logger or logging.getLogger(__name__)

    def create(self, data: MemoryCreate) -> Memory:
        """Create and return a memory."""
        memory_id = str(uuid4())
        now = utc_now()
        project_id = None

        with self._database.session() as connection:
            if data.project:
                project_id = self._ensure_project(connection, data.project)
            if data.session_id:
                self._ensure_session(connection, data.session_id)

            connection.execute(
                """
                INSERT INTO memories (
                    id, title, content, created_at, updated_at, source, importance,
                    project_id, session_id, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory_id,
                    data.title,
                    data.content,
                    datetime_to_text(now),
                    datetime_to_text(now),
                    data.source,
                    data.importance,
                    project_id,
                    data.session_id,
                    json.dumps(data.metadata, sort_keys=True),
                ),
            )
            self._replace_tags(connection, memory_id, data.tags)

        self._logger.info("memory_created id=%s title=%s", memory_id, data.title)
        return self.get(memory_id)  # type: ignore[return-value]

    def update(self, memory_id: str, data: MemoryUpdate) -> Memory | None:
        """Update a memory and return the updated record."""
        existing = self.get(memory_id)
        if existing is None:
            self._logger.warning("memory_update_missing id=%s", memory_id)
            return None

        title = data.title if data.title is not None else existing.title
        content = data.content if data.content is not None else existing.content
        source = data.source if data.source is not None else existing.source
        importance = data.importance if data.importance is not None else existing.importance
        metadata = data.metadata if data.metadata is not None else existing.metadata
        session_id = data.session_id if data.session_id is not None else existing.session_id
        project = data.project if data.project is not None else existing.project
        tags = data.tags if data.tags is not None else existing.tags

        with self._database.session() as connection:
            project_id = self._ensure_project(connection, project) if project else None
            if session_id:
                self._ensure_session(connection, session_id)
            connection.execute(
                """
                UPDATE memories
                SET title = ?,
                    content = ?,
                    updated_at = ?,
                    source = ?,
                    importance = ?,
                    project_id = ?,
                    session_id = ?,
                    metadata = ?
                WHERE id = ?
                """,
                (
                    title,
                    content,
                    datetime_to_text(utc_now()),
                    source,
                    importance,
                    project_id,
                    session_id,
                    json.dumps(metadata, sort_keys=True),
                    memory_id,
                ),
            )
            self._replace_tags(connection, memory_id, tags)

        self._logger.info("memory_updated id=%s", memory_id)
        return self.get(memory_id)

    def delete(self, memory_id: str) -> bool:
        """Delete a memory by ID."""
        with self._database.session() as connection:
            cursor = connection.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,),
            )
        deleted = cursor.rowcount > 0
        self._logger.info("memory_deleted id=%s deleted=%s", memory_id, deleted)
        return deleted

    def get(self, memory_id: str) -> Memory | None:
        """Return a memory by ID."""
        with self._database.session() as connection:
            row = connection.execute(
                """
                SELECT memories.*, projects.name AS project_name
                FROM memories
                LEFT JOIN projects ON projects.id = memories.project_id
                WHERE memories.id = ?
                """,
                (memory_id,),
            ).fetchone()
            if row is None:
                self._logger.info("memory_get id=%s found=false", memory_id)
                return None
            tags = self._tags_for_memory(connection, memory_id)

        self._logger.info("memory_get id=%s found=true", memory_id)
        return self._row_to_memory(row, tags)

    def list(self, limit: int = 100, offset: int = 0) -> tuple[Memory, ...]:
        """Return memories ordered by most recently updated."""
        with self._database.session() as connection:
            rows = connection.execute(
                """
                SELECT memories.*, projects.name AS project_name
                FROM memories
                LEFT JOIN projects ON projects.id = memories.project_id
                ORDER BY memories.updated_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
            memories = tuple(
                self._row_to_memory(row, self._tags_for_memory(connection, row["id"]))
                for row in rows
            )
        self._logger.info("memory_list count=%s limit=%s offset=%s", len(memories), limit, offset)
        return memories

    def count_memories(self) -> int:
        """Return the number of memory records."""
        with self._database.session() as connection:
            count = int(connection.execute("SELECT COUNT(*) FROM memories").fetchone()[0])
        self._logger.info("memory_count count=%s", count)
        return count

    def count_sessions(self) -> int:
        """Return the number of session records."""
        with self._database.session() as connection:
            return int(connection.execute("SELECT COUNT(*) FROM sessions").fetchone()[0])

    def statistics(self) -> MemoryStatistics:
        """Return operational memory database statistics."""
        return MemoryStatistics(
            total_memories=self.count_memories(),
            total_sessions=self.count_sessions(),
            database_size_bytes=self._database.size_bytes(),
            database_path=self._database.database_path,
        )

    def _ensure_project(self, connection: sqlite3.Connection, name: str) -> str:
        now = datetime_to_text(utc_now())
        existing = connection.execute(
            "SELECT id FROM projects WHERE name = ?",
            (name,),
        ).fetchone()
        if existing:
            return str(existing["id"])

        project_id = str(uuid4())
        connection.execute(
            """
            INSERT INTO projects (id, name, metadata, created_at, updated_at)
            VALUES (?, ?, '{}', ?, ?)
            """,
            (project_id, name, now, now),
        )
        return project_id

    def _ensure_session(self, connection: sqlite3.Connection, session_id: str) -> None:
        existing = connection.execute(
            "SELECT id FROM sessions WHERE id = ?",
            (session_id,),
        ).fetchone()
        if existing:
            return

        connection.execute(
            """
            INSERT INTO sessions (id, title, started_at, metadata)
            VALUES (?, ?, ?, '{}')
            """,
            (session_id, session_id, datetime_to_text(utc_now())),
        )

    def _replace_tags(
        self,
        connection: sqlite3.Connection,
        memory_id: str,
        tags: tuple[str, ...],
    ) -> None:
        connection.execute("DELETE FROM memory_tags WHERE memory_id = ?", (memory_id,))
        for tag_name in sorted({tag.strip() for tag in tags if tag.strip()}):
            tag_id = self._ensure_tag(connection, tag_name)
            connection.execute(
                "INSERT INTO memory_tags (memory_id, tag_id) VALUES (?, ?)",
                (memory_id, tag_id),
            )

    def _ensure_tag(self, connection: sqlite3.Connection, name: str) -> str:
        existing = connection.execute(
            "SELECT id FROM tags WHERE name = ?",
            (name,),
        ).fetchone()
        if existing:
            return str(existing["id"])

        tag_id = str(uuid4())
        connection.execute(
            "INSERT INTO tags (id, name, created_at) VALUES (?, ?, ?)",
            (tag_id, name, datetime_to_text(utc_now())),
        )
        return tag_id

    def _tags_for_memory(
        self,
        connection: sqlite3.Connection,
        memory_id: str,
    ) -> tuple[str, ...]:
        rows = connection.execute(
            """
            SELECT tags.name
            FROM tags
            INNER JOIN memory_tags ON memory_tags.tag_id = tags.id
            WHERE memory_tags.memory_id = ?
            ORDER BY tags.name ASC
            """,
            (memory_id,),
        ).fetchall()
        return tuple(str(row["name"]) for row in rows)

    def _row_to_memory(self, row: sqlite3.Row, tags: tuple[str, ...]) -> Memory:
        return Memory(
            id=str(row["id"]),
            title=str(row["title"]),
            content=str(row["content"]),
            created_at=datetime_from_text(str(row["created_at"])),
            updated_at=datetime_from_text(str(row["updated_at"])),
            source=str(row["source"]),
            importance=int(row["importance"]),
            tags=tags,
            project=row["project_name"],
            session_id=row["session_id"],
            metadata=json.loads(str(row["metadata"])),
        )
