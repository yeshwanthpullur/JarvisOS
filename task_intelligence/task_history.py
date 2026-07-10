"""Task intelligence history records."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field


@dataclass(slots=True)
class TaskHistoryRecord:
    entity_type: str
    entity_id: str
    event: str
    metadata: dict[str, object] = field(default_factory=dict)


class TaskHistory:
    """In-memory history for task intelligence."""

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._records: list[TaskHistoryRecord] = []
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("task_history_initialized")

    def record(
        self,
        entity_type: str,
        entity_id: str,
        event: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self._ensure_initialized()
        self._records.append(TaskHistoryRecord(entity_type, entity_id, event, dict(metadata or {})))
        self._logger.info("task_history_recorded entity_type=%s entity_id=%s event=%s", entity_type, entity_id, event)

    def count(self) -> int:
        self._ensure_initialized()
        return len(self._records)

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("TaskHistory must be initialized before use.")
