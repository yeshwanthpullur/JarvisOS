"""Task intelligence context objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from task_intelligence.models import TaskPriorityLevel


@dataclass(slots=True)
class TaskContext:
    """Runtime context for task intelligence operations."""

    project_id: str | None = None
    goal_id: str | None = None
    milestone_id: str | None = None
    task_id: str | None = None
    workflow_id: str | None = None
    conversation_id: str | None = None
    priority: TaskPriorityLevel = TaskPriorityLevel.NORMAL
    status: str = "created"
    dependencies: tuple[str, ...] = ()
    schedule: str | None = None
    progress: float = 0.0
    metadata: dict[str, object] = field(default_factory=dict)
    statistics: dict[str, object] = field(default_factory=dict)
