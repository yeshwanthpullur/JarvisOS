"""Rollback metadata for Agent Creator operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RollbackPlan:
    """Rollback strategy for a generated agent installation."""

    plan_id: str
    target_path: Path
    files_created: tuple[Path, ...] = ()
    files_replaced: tuple[Path, ...] = ()
    notes: tuple[str, ...] = ()


class RollbackManager:
    """Prepares rollback information without destructive behavior."""

    def __init__(self) -> None:
        self._plans: dict[str, RollbackPlan] = {}
        self.initialized = True

    def prepare(self, plan_id: str, target_path: Path, files: tuple[Path, ...]) -> RollbackPlan:
        """Prepare a rollback plan for files that will be created."""
        rollback = RollbackPlan(plan_id=plan_id, target_path=target_path, files_created=files)
        self._plans[plan_id] = rollback
        return rollback

    def get(self, plan_id: str) -> RollbackPlan | None:
        """Return rollback metadata."""
        return self._plans.get(plan_id)

