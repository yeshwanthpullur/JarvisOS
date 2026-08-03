"""Public facade for JARVIS OS persistent structured memory."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from memory.database import MemoryDatabase
from memory.models import (
    Memory,
    MemoryCreate,
    MemorySearchQuery,
    MemoryStatistics,
    MemoryUpdate,
    MemoryType,
    MemorySensitivity,
    MemoryStatus,
)
from memory.repository import MemoryRepository
from memory.search import MemorySearchService


class MemoryManager:
    """Coordinates database setup, repository operations, and memory search."""

    def __init__(
        self,
        storage_dir: Path,
        database_name: str = "jarvis_memory.db",
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._database = MemoryDatabase(storage_dir / database_name)
        self._repository = MemoryRepository(self._database, logger=self._logger)
        self._search = MemorySearchService(
            self._database,
            self._repository,
            logger=self._logger,
        )
        self.initialized = False

    @property
    def database_path(self) -> Path:
        """Return the SQLite database path."""
        return self._database.database_path

    def initialize(self) -> None:
        """Initialize and verify the SQLite memory database."""
        self._database.initialize()
        if not self._database.verify_schema():
            raise RuntimeError("Memory database schema verification failed.")
        self.initialized = True
        self._logger.info("memory_database_initialized path=%s", self.database_path)

    def verify_schema(self) -> bool:
        """Return whether the memory schema is available."""
        return self._database.verify_schema()

    def create_memory(
        self,
        title: str,
        content: str,
        source: str = "manual",
        importance: int = 1,
        tags: tuple[str, ...] = (),
        project: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        memory_type: str = MemoryType.CUSTOM_NOTE,
        sensitivity: str = MemorySensitivity.NORMAL,
        status: str = MemoryStatus.ACTIVE,
        confidence: float = 0.5,
        last_accessed_at: Any | None = None,
        access_count: int = 0,
        expiration_at: Any | None = None,
        supersedes_memory_id: str | None = None,
        related_goal_id: str | None = None,
        related_task_id: str | None = None,
        checksum: str | None = None,
        version: int = 1,
        user_confirmed: bool = False,
        normalized_content: str = "",
    ) -> Memory:
        """Create a persistent memory record."""
        self._ensure_initialized()
        return self._repository.create(
            MemoryCreate(
                title=title,
                content=content,
                source=source,
                importance=importance,
                tags=tags,
                project=project,
                session_id=session_id,
                metadata=metadata or {},
                memory_type=memory_type,
                sensitivity=sensitivity,
                status=status,
                confidence=confidence,
                last_accessed_at=last_accessed_at,
                access_count=access_count,
                expiration_at=expiration_at,
                supersedes_memory_id=supersedes_memory_id,
                related_goal_id=related_goal_id,
                related_task_id=related_task_id,
                checksum=checksum,
                version=version,
                user_confirmed=user_confirmed,
                normalized_content=normalized_content,
            )
        )

    def update_memory(
        self,
        memory_id: str,
        title: str | None = None,
        content: str | None = None,
        source: str | None = None,
        importance: int | None = None,
        tags: tuple[str, ...] | None = None,
        project: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        memory_type: str | None = None,
        sensitivity: str | None = None,
        status: str | None = None,
        confidence: float | None = None,
        last_accessed_at: Any | None = None,
        access_count: int | None = None,
        expiration_at: Any | None = None,
        supersedes_memory_id: str | None = None,
        related_goal_id: str | None = None,
        related_task_id: str | None = None,
        checksum: str | None = None,
        version: int | None = None,
        user_confirmed: bool | None = None,
        normalized_content: str | None = None,
    ) -> Memory | None:
        """Update a persistent memory record."""
        self._ensure_initialized()
        return self._repository.update(
            memory_id,
            MemoryUpdate(
                title=title,
                content=content,
                source=source,
                importance=importance,
                tags=tags,
                project=project,
                session_id=session_id,
                metadata=metadata,
                memory_type=memory_type,
                sensitivity=sensitivity,
                status=status,
                confidence=confidence,
                last_accessed_at=last_accessed_at,
                access_count=access_count,
                expiration_at=expiration_at,
                supersedes_memory_id=supersedes_memory_id,
                related_goal_id=related_goal_id,
                related_task_id=related_task_id,
                checksum=checksum,
                version=version,
                user_confirmed=user_confirmed,
                normalized_content=normalized_content,
            ),
        )

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a persistent memory record."""
        self._ensure_initialized()
        return self._repository.delete(memory_id)

    def search_memory(
        self,
        query: str,
        tags: tuple[str, ...] = (),
        project: str | None = None,
        session_id: str | None = None,
        limit: int = 20,
    ) -> tuple[Memory, ...]:
        """Search persistent structured memories."""
        self._ensure_initialized()
        return self._search.search(
            MemorySearchQuery(
                query=query,
                tags=tags,
                project=project,
                session_id=session_id,
                limit=limit,
            )
        )

    def list_memories(self, limit: int = 100, offset: int = 0) -> tuple[Memory, ...]:
        """List persistent memories."""
        self._ensure_initialized()
        return self._repository.list(limit=limit, offset=offset)

    def get_memory(self, memory_id: str) -> Memory | None:
        """Retrieve a memory by ID."""
        self._ensure_initialized()
        return self._repository.get(memory_id)

    def count_memories(self) -> int:
        """Return the total number of memories."""
        self._ensure_initialized()
        return self._repository.count_memories()

    def statistics(self) -> MemoryStatistics:
        """Return memory database statistics."""
        self._ensure_initialized()
        return self._repository.statistics()

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("MemoryManager must be initialized before use.")
