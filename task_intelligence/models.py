"""Shared task intelligence models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskPriorityLevel(str, Enum):
    """Priority levels for projects, goals, milestones, and tasks."""

    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    DEFERRED = "deferred"


@dataclass(slots=True)
class ProjectRecord:
    """Project metadata record."""

    project_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    goals: tuple[str, ...] = ()
    milestones: tuple[str, ...] = ()
    tasks: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    resources: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
    schedules: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    statistics: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class GoalRecord:
    """Goal metadata record."""

    goal_id: str = field(default_factory=lambda: str(uuid4()))
    project_id: str | None = None
    parent_goal_id: str | None = None
    name: str = ""
    description: str = ""
    purpose: str = ""
    desired_outcome: str = ""
    success_criteria: tuple[str, ...] = ()
    priority: TaskPriorityLevel = TaskPriorityLevel.NORMAL
    status: str = "created"
    target_date: str | None = None
    start_date: str | None = None
    completion_date: str | None = None
    progress: float = 0.0
    dependencies: tuple[str, ...] = ()
    blocker_references: tuple[str, ...] = ()
    related_goal_references: tuple[str, ...] = ()
    milestones: tuple[str, ...] = ()
    task_references: tuple[str, ...] = ()
    history: tuple[str, ...] = ()
    confidence: float = 0.5
    risk: str = ""
    feasibility: str = "unknown"
    time_horizon: str = "open_ended"
    review_frequency: str = "manual"
    last_reviewed: datetime | None = None
    next_review: datetime | None = None
    source: str = "task_intelligence"
    audit_metadata: dict[str, object] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class MilestoneRecord:
    """Milestone metadata record."""

    milestone_id: str = field(default_factory=lambda: str(uuid4()))
    project_id: str | None = None
    goal_id: str | None = None
    name: str = ""
    description: str = ""
    dependencies: tuple[str, ...] = ()
    progress: float = 0.0
    status: str = "created"
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
