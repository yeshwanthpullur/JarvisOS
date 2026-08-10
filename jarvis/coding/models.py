"""Typed, bounded models for the plan-only Coding Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4


MAX_TEXT = 1600
MAX_ITEMS = 24
MAX_FILE_NAME = 240


def _now() -> str:
    return datetime.now(UTC).isoformat()


class CodingIntent(StrEnum):
    EXPLAIN_CODE = "explain_code"
    INSPECT_REPO = "inspect_repo"
    PLAN_CHANGE = "plan_change"
    REVIEW_DIFF = "review_diff"
    TEST_PLAN = "test_plan"
    BUG_TRIAGE = "bug_triage"
    REFACTOR_PLAN = "refactor_plan"
    DOCUMENTATION_UPDATE = "documentation_update"
    DEPENDENCY_REVIEW = "dependency_review"
    RELEASE_REVIEW = "release_review"
    UNKNOWN = "unknown"


class CodingRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CodingStatus(StrEnum):
    PLANNED = "planned"
    INSPECTED = "inspected"
    REVIEWED = "reviewed"
    NEEDS_CLARIFICATION = "needs_clarification"
    NEEDS_APPROVAL = "needs_approval"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class CodingTask:
    request: str
    normalized_request: str
    intent: CodingIntent = CodingIntent.UNKNOWN
    scope: str = "repository"
    risk_level: CodingRiskLevel = CodingRiskLevel.LOW
    task_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        if not self.request.strip() or len(self.request) > MAX_TEXT:
            raise ValueError("invalid_coding_task")
        if len(self.normalized_request) > MAX_TEXT or len(self.scope) > 120:
            raise ValueError("coding_task_text_too_long")


@dataclass(frozen=True, slots=True)
class CodingPlan:
    task_id: str
    intent: CodingIntent
    summary: str
    proposed_steps: tuple[str, ...]
    likely_files: tuple[str, ...] = ()
    required_tests: tuple[str, ...] = ()
    risk_level: CodingRiskLevel = CodingRiskLevel.LOW
    approval_required: bool = False
    status: CodingStatus = CodingStatus.PLANNED
    warnings: tuple[str, ...] = ()
    plan_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if len(self.summary) > MAX_TEXT or not self.proposed_steps:
            raise ValueError("invalid_coding_plan")
        for values in (self.proposed_steps, self.likely_files, self.required_tests, self.warnings):
            if len(values) > MAX_ITEMS or any(len(str(item)) > MAX_TEXT for item in values):
                raise ValueError("coding_plan_limit_exceeded")


@dataclass(frozen=True, slots=True)
class RepoInspection:
    branch: str
    head: str
    tracked_clean: bool
    untracked_summary: tuple[str, ...] = ()
    staged_files: tuple[str, ...] = ()
    changed_files: tuple[str, ...] = ()
    recent_commits: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for values in (self.untracked_summary, self.staged_files, self.changed_files, self.recent_commits, self.warnings):
            if len(values) > MAX_ITEMS or any(len(str(item)) > MAX_FILE_NAME for item in values):
                raise ValueError("repo_inspection_limit_exceeded")


@dataclass(frozen=True, slots=True)
class DiffReview:
    files_changed: tuple[str, ...]
    insertions: int
    deletions: int
    summary: str
    risks: tuple[str, ...] = ()
    test_recommendations: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    review_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if min(self.insertions, self.deletions) < 0 or len(self.summary) > MAX_TEXT:
            raise ValueError("invalid_diff_review")
        for values in (self.files_changed, self.risks, self.test_recommendations, self.warnings):
            if len(values) > MAX_ITEMS or any(len(str(item)) > MAX_TEXT for item in values):
                raise ValueError("diff_review_limit_exceeded")


@dataclass(frozen=True, slots=True)
class CodingResult:
    request_id: str
    status: CodingStatus
    task: CodingTask | None = None
    plan: CodingPlan | None = None
    repo_inspection: RepoInspection | None = None
    diff_review: DiffReview | None = None
    output: str = ""
    warnings: tuple[str, ...] = ()
    error: str | None = None
    created_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        if len(self.output) > MAX_TEXT or len(self.error or "") > 240 or len(self.warnings) > MAX_ITEMS:
            raise ValueError("coding_result_limit_exceeded")
