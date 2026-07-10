"""Text search support for the JARVIS OS memory engine."""

from __future__ import annotations

import logging

from memory.database import MemoryDatabase
from memory.models import Memory, MemorySearchQuery
from memory.repository import MemoryRepository


class MemorySearchService:
    """Performs structured SQLite text search over memory records."""

    def __init__(
        self,
        database: MemoryDatabase,
        repository: MemoryRepository,
        logger: logging.Logger | None = None,
    ) -> None:
        self._database = database
        self._repository = repository
        self._logger = logger or logging.getLogger(__name__)

    def search(self, query: MemorySearchQuery) -> tuple[Memory, ...]:
        """Search memories by title/content with optional structured filters."""
        search_text = f"%{query.query.strip()}%"
        parameters: list[object] = [search_text, search_text]
        filters = [
            "(memories.title LIKE ? OR memories.content LIKE ?)",
        ]

        if query.project:
            filters.append("projects.name = ?")
            parameters.append(query.project)
        if query.session_id:
            filters.append("memories.session_id = ?")
            parameters.append(query.session_id)
        for tag in query.tags:
            filters.append(
                """
                EXISTS (
                    SELECT 1
                    FROM memory_tags mt
                    INNER JOIN tags t ON t.id = mt.tag_id
                    WHERE mt.memory_id = memories.id AND t.name = ?
                )
                """
            )
            parameters.append(tag)

        parameters.append(query.limit)
        where_clause = " AND ".join(filters)

        with self._database.session() as connection:
            rows = connection.execute(
                f"""
                SELECT memories.id
                FROM memories
                LEFT JOIN projects ON projects.id = memories.project_id
                WHERE {where_clause}
                ORDER BY memories.importance DESC, memories.updated_at DESC
                LIMIT ?
                """,
                tuple(parameters),
            ).fetchall()

        results = tuple(
            memory
            for row in rows
            if (memory := self._repository.get(str(row["id"]))) is not None
        )
        self._logger.info(
            "memory_search query=%s result_count=%s",
            query.query,
            len(results),
        )
        return results
