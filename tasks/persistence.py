"""Task persistence interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod

from tasks.schema import TaskSnapshot


class TaskPersistence(ABC):
    """Repository interface for saving and resuming task state."""

    @abstractmethod
    def save(self, snapshot: TaskSnapshot) -> None:
        """Persist the latest task snapshot."""

    @abstractmethod
    def load(self, task_id: str) -> TaskSnapshot | None:
        """Load a task snapshot by ID."""

    @abstractmethod
    def list_task_ids(self) -> tuple[str, ...]:
        """List persisted task IDs."""

    @abstractmethod
    def delete(self, task_id: str) -> None:
        """Delete a persisted task snapshot."""

