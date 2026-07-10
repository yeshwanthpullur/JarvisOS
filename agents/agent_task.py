"""Agent task delegation models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class AgentTask:
    """Delegated task metadata for future execution."""

    task_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    parent_task_id: str | None = None
    child_task_ids: tuple[str, ...] = ()
    subtask_ids: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    prerequisites: tuple[str, ...] = ()
    completion_status: str = "pending"
    priority: int = 100
    deadline: datetime | None = None
    assigned_agent: str | None = None
    cancellation_requested: bool = False
    rollback_metadata: dict[str, Any] = field(default_factory=dict)
    retry_metadata: dict[str, Any] = field(default_factory=dict)
    execution_result: dict[str, Any] = field(default_factory=dict)
