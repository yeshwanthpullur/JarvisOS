"""SQLite database setup for the JARVIS OS memory engine."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


SCHEMA_VERSION = 1
REQUIRED_TABLES = ("memories", "sessions", "projects", "tags", "relationships")


class MemoryDatabase:
    """Owns SQLite connections, schema creation, and schema verification."""

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
        """Create the memory database schema if it does not already exist."""
        with self.session() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    metadata TEXT NOT NULL DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    importance INTEGER NOT NULL DEFAULT 1,
                    project_id TEXT,
                    session_id TEXT,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    embedding_model TEXT,
                    embedding_dimensions INTEGER,
                    embedding BLOB,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                        ON UPDATE CASCADE ON DELETE SET NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id)
                        ON UPDATE CASCADE ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS tags (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS memory_tags (
                    memory_id TEXT NOT NULL,
                    tag_id TEXT NOT NULL,
                    PRIMARY KEY (memory_id, tag_id),
                    FOREIGN KEY (memory_id) REFERENCES memories(id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
                    FOREIGN KEY (tag_id) REFERENCES tags(id)
                        ON UPDATE CASCADE ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS relationships (
                    id TEXT PRIMARY KEY,
                    source_memory_id TEXT NOT NULL,
                    target_memory_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (source_memory_id) REFERENCES memories(id)
                        ON UPDATE CASCADE ON DELETE CASCADE,
                    FOREIGN KEY (target_memory_id) REFERENCES memories(id)
                        ON UPDATE CASCADE ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_memories_created_at
                    ON memories(created_at);
                CREATE INDEX IF NOT EXISTS idx_memories_updated_at
                    ON memories(updated_at);
                CREATE INDEX IF NOT EXISTS idx_memories_source
                    ON memories(source);
                CREATE INDEX IF NOT EXISTS idx_memories_project_id
                    ON memories(project_id);
                CREATE INDEX IF NOT EXISTS idx_memories_session_id
                    ON memories(session_id);
                CREATE INDEX IF NOT EXISTS idx_tags_name
                    ON tags(name);
                """
            )
            connection.execute(
                """
                INSERT INTO schema_metadata (key, value)
                VALUES ('schema_version', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (str(SCHEMA_VERSION),),
            )

    def verify_schema(self) -> bool:
        """Return whether all required memory tables exist."""
        with self.session() as connection:
            existing = {
                row["name"]
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    """
                )
            }
        return set(REQUIRED_TABLES).issubset(existing)

    def size_bytes(self) -> int:
        """Return the current database file size in bytes."""
        if not self.database_path.exists():
            return 0
        return self.database_path.stat().st_size
