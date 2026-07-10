"""Workflow scheduling architecture."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class WorkflowScheduleMode(StrEnum):
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    QUEUED = "queued"
    PRIORITY = "priority"
    DEPENDENCY_AWARE = "dependency_aware"
    RETRY_QUEUE = "retry_queue"
    RECOVERY_QUEUE = "recovery_queue"
    CRON = "cron"


@dataclass(frozen=True, slots=True)
class WorkflowSchedule:
    workflow_id: str
    mode: WorkflowScheduleMode
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowScheduler:
    initialized = True

    def schedule(self, workflow_id: str, mode: WorkflowScheduleMode = WorkflowScheduleMode.IMMEDIATE) -> WorkflowSchedule:
        return WorkflowSchedule(workflow_id=workflow_id, mode=mode, metadata={})
