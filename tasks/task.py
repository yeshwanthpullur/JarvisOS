"""Core task models for JARVIS OS."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from tasks.priority import TaskPriority
from tasks.status import TaskStatus


def utc_now() -> datetime:
    """Return the current UTC time."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class TaskLogEntry:
    """Structured log entry attached to a task."""

    timestamp: datetime
    message: str
    level: str = "INFO"


@dataclass(slots=True)
class Task:
    """A unit of work in JARVIS OS.

    Future agents must create tasks instead of directly performing work. This
    model stores task state only; it does not execute work.
    """

    task_id: str
    name: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    dependencies: tuple[str, ...] = ()
    assigned_agent: str | None = None
    related_memories: tuple[str, ...] = ()
    input_files: tuple[Path, ...] = ()
    output_files: tuple[Path, ...] = ()
    logs: tuple[TaskLogEntry, ...] = ()
    retry_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_log(self, message: str, level: str = "INFO") -> None:
        """Append a structured task log entry."""
        self.logs = (
            *self.logs,
            TaskLogEntry(timestamp=utc_now(), message=message, level=level),
        )


@dataclass(frozen=True, slots=True)
class TaskCreate:
    """Input model for creating a task."""

    name: str
    description: str
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: tuple[str, ...] = ()
    assigned_agent: str | None = None
    related_memories: tuple[str, ...] = ()
    input_files: tuple[Path, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


def create_task_model(data: TaskCreate) -> Task:
    """Create a task model from user-provided task input."""
    task = Task(
        task_id=str(uuid4()),
        name=data.name,
        description=data.description,
        priority=data.priority,
        status=TaskStatus.PENDING,
        created_at=utc_now(),
        dependencies=data.dependencies,
        assigned_agent=data.assigned_agent,
        related_memories=data.related_memories,
        input_files=data.input_files,
        metadata=dict(data.metadata),
    )
    task.add_log("Task created.")
    return task

