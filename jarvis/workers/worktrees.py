"""Approval-delegated Git worktree isolation for modifying workers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
from typing import Callable

from .models import WorktreePlan, bounded


AuthorizationCheck = Callable[[str, tuple[str, ...]], bool]


def deny_authorization(_operation: str, _resources: tuple[str, ...]) -> bool:
    return False


class WorktreeIsolationManager:
    def __init__(self, repo_root: Path, workspace_root: Path, authorization_check: AuthorizationCheck = deny_authorization) -> None:
        self.repo_root = repo_root.resolve()
        self.workspace_root = workspace_root.resolve()
        self.authorization_check = authorization_check
        self._plans: dict[str, WorktreePlan] = {}
        self._artifacts: dict[str, tuple[str, ...]] = {}

    @staticmethod
    def _slug(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")[:40]
        return slug or "work"

    def plan(self, task_id: str, title: str) -> WorktreePlan:
        slug = self._slug(title)
        branch = f"jarvis/task-{self._slug(task_id)}-{slug}"[:120]
        workspace = f"worktrees/{self._slug(task_id)}-{slug}"
        plan = WorktreePlan(task_id, branch, workspace, "planned", True, False, "explicit_after_review", "Creation and cleanup require delegated Approval/Broker authorization; merge is never automatic.")
        self._plans[task_id] = plan
        return plan

    def validate(self, plan: WorktreePlan) -> tuple[str, ...]:
        errors = []
        if not plan.branch_name.startswith("jarvis/task-"):
            errors.append("invalid_worker_branch")
        target = (self.workspace_root / Path(plan.workspace_reference).name).resolve()
        try:
            target.relative_to(self.workspace_root)
        except ValueError:
            errors.append("workspace_escape_blocked")
        if plan.auto_merge:
            errors.append("automatic_merge_blocked")
        return tuple(errors)

    def create(self, task_id: str, base_ref: str = "HEAD") -> WorktreePlan:
        plan = self._plans[task_id]
        if self.validate(plan):
            return WorktreePlan(plan.task_id, plan.branch_name, plan.workspace_reference, "blocked", reason="Invalid worktree plan.")
        resources = (plan.branch_name, plan.workspace_reference, bounded(base_ref, 120))
        if not self.authorization_check("git_worktree_create", resources):
            return WorktreePlan(plan.task_id, plan.branch_name, plan.workspace_reference, "approval_required", reason="Existing Approval/Broker authority did not authorize worktree creation.")
        target = self.workspace_root / Path(plan.workspace_reference).name
        target.parent.mkdir(parents=True, exist_ok=True)
        process = subprocess.run(["git", "worktree", "add", "-b", plan.branch_name, str(target), base_ref], cwd=self.repo_root, capture_output=True, text=True, timeout=30, shell=False)
        status = "created" if process.returncode == 0 else "failed"
        result = WorktreePlan(plan.task_id, plan.branch_name, plan.workspace_reference, status, reason="Worktree created under delegated authorization." if status == "created" else bounded(process.stderr, 300))
        self._plans[task_id] = result
        return result

    def cleanup(self, task_id: str) -> WorktreePlan:
        plan = self._plans[task_id]
        if not self.authorization_check("git_worktree_cleanup", (plan.branch_name, plan.workspace_reference)):
            return WorktreePlan(plan.task_id, plan.branch_name, plan.workspace_reference, "approval_required", reason="Explicit cleanup authorization is required.")
        target = self.workspace_root / Path(plan.workspace_reference).name
        process = subprocess.run(["git", "worktree", "remove", str(target)], cwd=self.repo_root, capture_output=True, text=True, timeout=30, shell=False)
        status = "cleaned" if process.returncode == 0 else "failed"
        result = WorktreePlan(plan.task_id, plan.branch_name, plan.workspace_reference, status, reason="Worktree cleaned; branch was retained for review." if status == "cleaned" else bounded(process.stderr, 300))
        self._plans[task_id] = result
        return result

    def stale(self) -> tuple[WorktreePlan, ...]:
        return tuple(plan for plan in self._plans.values() if plan.status == "created" and not (self.workspace_root / Path(plan.workspace_reference).name).exists())

    def map_artifact(self, task_id: str, artifact_ref: str) -> WorktreePlan:
        plan = self._plans[task_id]
        if len(artifact_ref) > 240 or Path(artifact_ref).is_absolute() or ".." in Path(artifact_ref).parts:
            raise ValueError("unsafe_worktree_artifact_reference")
        values = (self._artifacts.get(task_id, ()) + (artifact_ref,))[-32:]
        self._artifacts[task_id] = values
        updated = WorktreePlan(
            plan.task_id, plan.branch_name, plan.workspace_reference, plan.status,
            plan.requires_approval, plan.auto_merge, plan.cleanup_policy, plan.reason, values,
        )
        self._plans[task_id] = updated
        return updated
