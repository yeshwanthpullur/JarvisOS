"""Plan-only Coding Agent with read-only repository diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from .diff import DiffReviewer
from .models import CodingResult, CodingStatus
from .planner import CodingPlanner
from .repo import RepoInspector
from .safety import evaluate_coding_safety
from .storage import CodingHistoryRecord, CodingHistoryStore


@dataclass(slots=True)
class CodingAgent:
    repo_inspector: RepoInspector
    diff_reviewer: DiffReviewer
    planner: CodingPlanner = field(default_factory=CodingPlanner)
    history_store: CodingHistoryStore | None = None
    enabled: bool = True
    default_mode: str = "plan_only"
    allow_write_operations: bool = False
    allow_command_execution: bool = False
    require_approval_for_write: bool = True
    require_approval_for_push: bool = True
    block_secrets_access: bool = True
    max_history_items: int = 25
    history: list[CodingResult] = field(default_factory=list)
    last_history_error: str | None = None

    def __post_init__(self) -> None:
        self.max_history_items = max(1, min(int(self.max_history_items), 100))

    def _record(self, result: CodingResult) -> CodingResult:
        self.history = (self.history + [result])[-self.max_history_items :]
        if self.history_store is not None:
            try:
                existing = self.history_store.load()
                task = result.task
                record = CodingHistoryRecord(result.request_id, task.intent.value if task else "unknown", result.status.value, task.risk_level.value if task else "low", result.created_at)
                self.history_store.save(existing + (record,))
                self.last_history_error = None
            except (OSError, ValueError, TypeError):
                self.last_history_error = "CODING_HISTORY_WRITE_FAILED"
        return result

    def plan(self, request: str) -> CodingResult:
        if not self.enabled:
            return self._record(CodingResult(str(uuid4()), CodingStatus.UNAVAILABLE, error="coding_agent_disabled"))
        task, plan = self.planner.create_plan(request)
        error = "coding_request_blocked" if plan.status is CodingStatus.BLOCKED else None
        return self._record(CodingResult(str(uuid4()), plan.status, task=task, plan=plan, warnings=plan.warnings, error=error))

    def inspect(self) -> CodingResult:
        inspection = self.repo_inspector.inspect()
        status = CodingStatus.UNAVAILABLE if inspection.branch == "unavailable" else CodingStatus.INSPECTED
        return self._record(CodingResult(str(uuid4()), status, repo_inspection=inspection, warnings=inspection.warnings, error="git_unavailable" if status is CodingStatus.UNAVAILABLE else None))

    def review(self) -> CodingResult:
        review = self.diff_reviewer.review()
        return self._record(CodingResult(str(uuid4()), CodingStatus.REVIEWED, diff_review=review, warnings=review.warnings))

    def risk(self, request: str):
        return evaluate_coding_safety(request)

    def show(self, request_id: str) -> CodingResult | None:
        return next((item for item in reversed(self.history) if item.request_id == request_id), None)

    def show_record(self, request_id: str) -> CodingHistoryRecord | None:
        return next((item for item in reversed(self.history_records()) if item.request_id == request_id), None)

    def history_records(self) -> tuple[CodingHistoryRecord, ...]:
        if self.history_store is not None:
            return self.history_store.load()
        return tuple(CodingHistoryRecord(item.request_id, item.task.intent.value if item.task else "unknown", item.status.value, item.task.risk_level.value if item.task else "low", item.created_at) for item in self.history)

    def status(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "status": "ready_plan_only" if self.enabled else "disabled",
            "default_mode": self.default_mode,
            "write_operations": "disabled" if not self.allow_write_operations else "approval_gated",
            "command_execution": "disabled" if not self.allow_command_execution else "approval_gated",
            "write_approval_required": self.require_approval_for_write,
            "push_approval_required": self.require_approval_for_push,
            "secrets_access": "blocked" if self.block_secrets_access else "policy_required",
            "history_status": "error" if self.last_history_error else "ready",
        }
