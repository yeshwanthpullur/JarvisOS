"""Workflow recovery architecture."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class WorkflowFailureClass(StrEnum):
    UNKNOWN = "unknown"
    DEPENDENCY = "dependency"
    EXECUTION = "execution"
    TIMEOUT = "timeout"
    VALIDATION = "validation"


@dataclass(frozen=True, slots=True)
class WorkflowRecoveryPlan:
    classification: WorkflowFailureClass
    actions: tuple[str, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowRecovery:
    initialized = True

    def __init__(self) -> None:
        self._plans: list[WorkflowRecoveryPlan] = []

    def classify_failure(self, message: str) -> WorkflowFailureClass:
        lowered = message.lower()
        if "timeout" in lowered:
            return WorkflowFailureClass.TIMEOUT
        if "dependency" in lowered:
            return WorkflowFailureClass.DEPENDENCY
        if "validation" in lowered:
            return WorkflowFailureClass.VALIDATION
        if "execution" in lowered:
            return WorkflowFailureClass.EXECUTION
        return WorkflowFailureClass.UNKNOWN

    def plan(self, message: str) -> WorkflowRecoveryPlan:
        plan = WorkflowRecoveryPlan(self.classify_failure(message), ("retry_step", "retry_workflow", "rollback", "resume"))
        self._plans.append(plan)
        return plan

    def statistics(self) -> dict[str, int]:
        return {"recovery_plans": len(self._plans)}
