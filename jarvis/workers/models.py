"""Bounded records for external workers and controlled work planning."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
import re
from typing import Mapping
from uuid import uuid4


MAX_TEXT = 1000
MAX_ITEMS = 32
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key|access[_-]?token|authorization|password|secret|cookie|credential)\s*[:=]\s*\S+"
)
PRIVATE_PATH_PATTERN = re.compile(r"(?i)(?<![\w])(?:[A-Z]:[\\/][^\s,;]+|/(?:home|users)/[^\s,;]+)")


def now() -> str:
    return datetime.now(UTC).isoformat()


def bounded(value: object, limit: int = MAX_TEXT) -> str:
    text = " ".join(str(value or "").split())
    text = SECRET_PATTERN.sub("[REDACTED]", text)
    text = PRIVATE_PATH_PATTERN.sub("[PRIVATE_PATH]", text)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def bounded_items(values: tuple[str, ...], limit: int = MAX_ITEMS) -> tuple[str, ...]:
    return tuple(bounded(value, 240) for value in values[:limit])


class WorkerStatus(StrEnum):
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"
    ERROR = "error"


class WorkspaceMode(StrEnum):
    READ_ONLY = "read_only"
    WORKTREE = "worktree"
    ISOLATED_EXTERNAL = "isolated_external"
    UNAVAILABLE = "unavailable"


class WorkerTaskStatus(StrEnum):
    QUEUED = "queued"
    PLANNING = "planning"
    PLANNED = "planned"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    REVIEWING = "reviewing"
    RETRYING = "retrying"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    FAILED = "failed"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"


class WorkerErrorCode(StrEnum):
    AGENT_NOT_INSTALLED = "agent_not_installed"
    AGENT_NOT_AUTHENTICATED = "agent_not_authenticated"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    WORKSPACE_INVALID = "workspace_invalid"
    PERMISSION_DENIED = "permission_denied"
    TASK_TIMEOUT = "task_timeout"
    AGENT_CRASHED = "agent_crashed"
    UNSUPPORTED_CAPABILITY = "unsupported_capability"
    WORKER_MISMATCH = "worker_mismatch"
    WORKER_UNAVAILABLE = "worker_unavailable"
    EXECUTION_NOT_AUTHORIZED = "execution_not_authorized"


class RoutingMode(StrEnum):
    LOCAL_ONLY = "local_only"
    PRIVATE_HYBRID = "private_hybrid"
    NORMAL_HYBRID = "normal_hybrid"
    CLOUD_MAX = "cloud_max"


class MessageKind(StrEnum):
    FINDING = "finding"
    QUESTION = "question"
    REQUEST = "request"
    ARTIFACT = "artifact"
    BLOCKER = "blocker"
    REVIEW = "review"
    REJECTION = "rejection"
    APPROVAL_REQUEST = "approval_request"
    COMPLETION_CLAIM = "completion_claim"


class ContextScope(StrEnum):
    SESSION = "session"
    TASK = "task"
    PROJECT = "project"
    KNOWLEDGE = "knowledge"
    PERSONAL_REFERENCE = "personal_reference"


@dataclass(frozen=True, slots=True)
class WorkerCapabilities:
    planning: bool = True
    repository_read: bool = False
    repository_write: bool = False
    streaming: bool = False
    cancellation: bool = False
    resume: bool = False
    artifact_collection: bool = False
    model_discovery: bool = False
    independent_review: bool = False
    sessions: bool = True
    tool_use: bool = False
    research: bool = False
    local_models: bool = False
    cloud_models: bool = False
    supported_task_types: tuple[str, ...] = ("planning",)


@dataclass(frozen=True, slots=True)
class WorkerRecord:
    worker_id: str
    display_name: str
    adapter_type: str
    executable_candidates: tuple[str, ...]
    status: WorkerStatus = WorkerStatus.UNAVAILABLE
    detected_version: str = ""
    discovery_source: str = "not_checked"
    capabilities: WorkerCapabilities = field(default_factory=WorkerCapabilities)
    workspace_modes: tuple[WorkspaceMode, ...] = (WorkspaceMode.READ_ONLY,)
    local_only: bool = True
    execution_enabled: bool = False
    approval_required: bool = True
    authority: str = "external_worker_only"
    health_reason: str = "Not detected."
    model_ids: tuple[str, ...] = ()
    executable: str = ""
    detected: bool = False
    configured: bool = False
    authenticated: bool = False
    healthy: bool = False
    workspace_policy: str = "explicit_bounded_workspace"
    permission_policy: str = "approval_policy_broker_required"
    cost_class: str = "unknown"
    availability: str = "unavailable"
    last_health_check: str = ""

    def __post_init__(self) -> None:
        if not self.worker_id or len(self.worker_id) > 80:
            raise ValueError("invalid_worker_id")
        if len(self.display_name) > 120 or len(self.health_reason) > 500:
            raise ValueError("worker_metadata_too_large")
        if self.status is WorkerStatus.READY and not self.execution_enabled:
            raise ValueError("ready_worker_requires_execution_enablement")
        if len(self.model_ids) > MAX_ITEMS:
            raise ValueError("worker_model_limit_exceeded")


@dataclass(frozen=True, slots=True)
class WorkerTask:
    objective: str
    worker_id: str
    execution_mode: str = "plan_only"
    workspace_mode: WorkspaceMode = WorkspaceMode.READ_ONLY
    task_id: str = field(default_factory=lambda: f"worker-{uuid4().hex[:12]}")
    context_refs: tuple[str, ...] = ()
    approval_ref: str = ""
    timeout_seconds: int = 120
    max_output_chars: int = 8000
    created_at: str = field(default_factory=now)
    workspace_reference: str = ""
    allowed_capabilities: tuple[str, ...] = ("planning", "metadata_read")
    denied_capabilities: tuple[str, ...] = ("secrets_access", "permission_change", "main_branch_write")
    budget_reference: str = "bounded_default"
    expected_outputs: tuple[str, ...] = ("structured_result",)
    completion_criteria: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.objective.strip() or len(self.objective) > 4000:
            raise ValueError("invalid_worker_objective")
        if not self.worker_id or len(self.worker_id) > 80:
            raise ValueError("invalid_worker_id")
        if self.execution_mode not in {"plan_only", "dry_run", "approved_execution", "blocked"}:
            raise ValueError("invalid_worker_execution_mode")
        if not 1 <= self.timeout_seconds <= 3600 or not 256 <= self.max_output_chars <= 100_000:
            raise ValueError("invalid_worker_bounds")
        if len(self.context_refs) > MAX_ITEMS:
            raise ValueError("worker_context_limit_exceeded")
        if any(len(values) > MAX_ITEMS for values in (self.allowed_capabilities, self.denied_capabilities, self.expected_outputs, self.completion_criteria)):
            raise ValueError("worker_task_item_limit_exceeded")
        if set(self.allowed_capabilities).intersection(self.denied_capabilities):
            raise ValueError("conflicting_worker_capabilities")
        if self.workspace_mode is not WorkspaceMode.READ_ONLY and not self.workspace_reference:
            raise ValueError("worker_workspace_reference_required")
        if PathLikeUnsafe.is_unsafe(self.workspace_reference):
            raise ValueError("unsafe_worker_workspace_reference")


@dataclass(frozen=True, slots=True)
class WorkerError:
    code: WorkerErrorCode | str
    message: str
    retryable: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", WorkerErrorCode(self.code))
        object.__setattr__(self, "message", bounded(self.message, 500))


@dataclass(frozen=True, slots=True)
class WorkerArtifact:
    artifact_id: str
    artifact_type: str
    safe_reference: str
    checksum: str = ""
    trusted: bool = False

    def __post_init__(self) -> None:
        if not self.artifact_id or PathLikeUnsafe.is_unsafe(self.safe_reference):
            raise ValueError("unsafe_worker_artifact")
        if len(self.artifact_id) > 80 or len(self.artifact_type) > 80 or len(self.safe_reference) > 300:
            raise ValueError("worker_artifact_metadata_too_large")


@dataclass(frozen=True, slots=True)
class WorkerResult:
    task_id: str
    worker_id: str
    status: WorkerTaskStatus
    summary: str = ""
    artifacts: tuple[WorkerArtifact, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    error: WorkerError | None = None
    started_at: str = ""
    finished_at: str = field(default_factory=now)
    response: str = ""
    files_changed: tuple[str, ...] = ()
    proposed_commands: tuple[str, ...] = ()
    usage: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "summary", bounded(self.summary, 8000))
        object.__setattr__(self, "warnings", bounded_items(self.warnings))
        object.__setattr__(self, "response", bounded(self.response, 8000))
        if len(self.artifacts) > MAX_ITEMS or len(self.evidence_refs) > MAX_ITEMS or len(self.files_changed) > MAX_ITEMS or len(self.proposed_commands) > MAX_ITEMS or len(self.usage) > MAX_ITEMS:
            raise ValueError("worker_result_item_limit_exceeded")
        object.__setattr__(self, "evidence_refs", bounded_items(self.evidence_refs))
        object.__setattr__(self, "files_changed", bounded_items(self.files_changed))
        object.__setattr__(self, "proposed_commands", bounded_items(self.proposed_commands))
        object.__setattr__(self, "usage", safe_metadata(self.usage))


@dataclass(frozen=True, slots=True)
class ProviderRecord:
    provider_id: str
    provider_type: str
    locality: str
    status: str
    credential_reference: str = ""
    enabled: bool = False
    cost_class: str = "unknown"
    privacy_class: str = "metadata_only"
    capabilities: tuple[str, ...] = ()
    reason: str = ""
    base_reference: str = ""
    configured: bool = False
    health: str = "not_checked"
    rate_limit_metadata: str = "unknown"
    model_ids: tuple[str, ...] = ()
    last_health_check: str = ""

    def __post_init__(self) -> None:
        if len(self.reason) > 500 or len(self.capabilities) > MAX_ITEMS:
            raise ValueError("provider_metadata_limit_exceeded")
        if self.credential_reference and not self.credential_reference.endswith("_ENV"):
            raise ValueError("credential_reference_must_be_symbolic")


@dataclass(frozen=True, slots=True)
class DynamicModelRecord:
    model_id: str
    provider_id: str
    status: str = "available"
    aliases: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ("chat", "coding")
    context_window: int | None = None
    cost_class: str = "unknown"
    exact_price_known: bool = False
    free: bool | None = None
    temporary: bool = False
    deprecated: bool = False
    discovered_at: str = field(default_factory=now)
    source: str = "runtime_discovery"
    reason: str = ""
    display_name: str = ""
    reasoning: bool = True
    coding: bool = True
    vision: bool = False
    tool_use: bool = False
    structured_output: bool = False
    context_metadata: str = "unknown"
    speed_class: str = "unknown"
    privacy_class: str = "provider_dependent"
    locality: str = "unknown"
    last_seen: str = ""
    last_checked: str = ""
    expires_at: str = ""

    def __post_init__(self) -> None:
        if not self.model_id or len(self.model_id) > 180:
            raise ValueError("invalid_model_id")
        if not re.fullmatch(r"[A-Za-z0-9@._+:/-]+", self.model_id):
            raise ValueError("unsafe_model_id")
        if len(self.aliases) > 16 or len(self.capabilities) > 16:
            raise ValueError("model_metadata_limit_exceeded")


@dataclass(frozen=True, slots=True)
class ModelAlias:
    alias: str
    target_model_id: str | None
    status: str
    reason: str
    possible_successor: str | None = None
    last_checked: str = field(default_factory=now)
    source: str = "runtime_discovery"


@dataclass(frozen=True, slots=True)
class RouteRequest:
    task_type: str
    privacy_mode: RoutingMode = RoutingMode.LOCAL_ONLY
    preferred_worker: str = ""
    preferred_model: str = ""
    requires_repository_write: bool = False
    independent_review: bool = False
    max_cost_class: str = "free_or_unknown"
    online: bool = True
    max_latency_class: str = "any"
    per_request_budget: str = "unspecified"
    per_task_budget: str = "unspecified"
    provider_spending_cap: str = "unspecified"
    risk_level: str = "low"
    workspace_requirement: WorkspaceMode = WorkspaceMode.READ_ONLY


@dataclass(frozen=True, slots=True)
class RouteDecision:
    status: str
    worker_id: str | None
    provider_id: str | None
    model_id: str | None
    reason: str
    fallback_worker_ids: tuple[str, ...] = ()
    reviewer_worker_id: str | None = None
    approval_required: bool = False
    execution_mode: str = "plan_only"
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class Goal:
    title: str
    success_criteria: tuple[str, ...]
    goal_id: str = field(default_factory=lambda: f"goal-{uuid4().hex[:12]}")
    status: str = "planned"


@dataclass(frozen=True, slots=True)
class Project:
    name: str
    goal_refs: tuple[str, ...]
    project_id: str = field(default_factory=lambda: f"project-{uuid4().hex[:12]}")


@dataclass(frozen=True, slots=True)
class Milestone:
    title: str
    project_ref: str
    milestone_id: str = field(default_factory=lambda: f"milestone-{uuid4().hex[:12]}")
    status: str = "planned"


@dataclass(frozen=True, slots=True)
class Task:
    title: str
    owner_worker_id: str
    dependencies: tuple[str, ...] = ()
    task_id: str = field(default_factory=lambda: f"task-{uuid4().hex[:12]}")
    status: WorkerTaskStatus = WorkerTaskStatus.QUEUED
    timeout_seconds: int = 180
    risk: str = "low"
    parallel_safe: bool = False
    required_capabilities: tuple[str, ...] = ()
    completion_criteria: tuple[str, ...] = ()
    retry_count: int = 0
    max_retries: int = 1
    priority: str = "normal"

    def __post_init__(self) -> None:
        if not self.title.strip() or len(self.title) > 500 or not self.owner_worker_id or len(self.owner_worker_id) > 80:
            raise ValueError("invalid_work_task")
        if len(self.dependencies) > MAX_ITEMS or len(self.required_capabilities) > MAX_ITEMS or len(self.completion_criteria) > MAX_ITEMS:
            raise ValueError("work_task_item_limit_exceeded")
        if not 1 <= self.timeout_seconds <= 3600 or not 0 <= self.retry_count <= self.max_retries <= 5:
            raise ValueError("invalid_work_task_bounds")


@dataclass(frozen=True, slots=True)
class Subtask:
    title: str
    parent_task_ref: str
    subtask_id: str = field(default_factory=lambda: f"subtask-{uuid4().hex[:12]}")


@dataclass(frozen=True, slots=True)
class AgentRun:
    task_ref: str
    worker_id: str
    run_id: str = field(default_factory=lambda: f"run-{uuid4().hex[:12]}")
    status: WorkerTaskStatus = WorkerTaskStatus.PLANNED


@dataclass(frozen=True, slots=True)
class Review:
    task_ref: str
    reviewer_worker_id: str
    verdict: str = "pending"
    review_id: str = field(default_factory=lambda: f"review-{uuid4().hex[:12]}")


@dataclass(frozen=True, slots=True)
class Approval:
    task_ref: str
    approval_ref: str
    state: str = "required"


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: str
    source_ref: str
    claim: str
    trust: str = "untrusted"


@dataclass(frozen=True, slots=True)
class Result:
    task_ref: str
    status: WorkerTaskStatus
    evidence_refs: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    summary: str = ""


@dataclass(frozen=True, slots=True)
class StructuredMessage:
    session_id: str
    task_id: str
    sender: str
    receiver: str
    kind: MessageKind
    payload_ref: str
    trust: str = "untrusted"
    privacy_scope: tuple[str, ...] = ("task",)
    correlation_id: str = ""
    evidence_refs: tuple[str, ...] = ()
    status_metadata: tuple[tuple[str, str], ...] = ()
    message_id: str = field(default_factory=lambda: f"msg-{uuid4().hex[:12]}")
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if SECRET_PATTERN.search(self.payload_ref) or PathLikeUnsafe.is_unsafe(self.payload_ref) or len(self.payload_ref) > 500:
            raise ValueError("unsafe_worker_message")
        if self.sender == self.receiver:
            raise ValueError("self_message_blocked")
        if len(self.evidence_refs) > 16 or len(self.status_metadata) > 16:
            raise ValueError("worker_message_metadata_limit_exceeded")


@dataclass(frozen=True, slots=True)
class ContextFragment:
    scope: ContextScope
    reference: str
    provenance: str
    trust: str = "untrusted"
    contains_personal_data: bool = False
    char_budget: int = 1000

    def __post_init__(self) -> None:
        if len(self.reference) > 300 or len(self.provenance) > 300:
            raise ValueError("context_fragment_too_large")
        if PathLikeUnsafe.is_unsafe(self.reference) or PathLikeUnsafe.is_unsafe(self.provenance):
            raise ValueError("unsafe_context_reference")
        if self.scope is ContextScope.PERSONAL_REFERENCE and not self.contains_personal_data:
            raise ValueError("personal_scope_requires_explicit_classification")


@dataclass(frozen=True, slots=True)
class WorktreePlan:
    task_id: str
    branch_name: str
    workspace_reference: str
    status: str
    requires_approval: bool = True
    auto_merge: bool = False
    cleanup_policy: str = "explicit_after_review"
    reason: str = ""
    artifact_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WorkRuntimeLimits:
    enabled: bool = True
    default_mode: str = "plan_only"
    default_routing_mode: str = "local_only"
    max_workers: int = 16
    max_parallel_tasks: int = 2
    max_tasks: int = 64
    max_messages: int = 200
    max_context_fragments: int = 64
    max_context_chars: int = 12_000
    default_timeout_seconds: int = 180
    max_fallbacks: int = 2
    allow_cloud_routes: bool = False
    require_approval_for_writes: bool = True
    worktree_auto_merge: bool = False

    def __post_init__(self) -> None:
        if self.default_mode not in {"plan_only", "dry_run"}:
            raise ValueError("unsafe_worker_default_mode")
        if self.default_routing_mode not in {item.value for item in RoutingMode}:
            raise ValueError("invalid_worker_routing_mode")
        if not 1 <= self.max_workers <= 64 or not 1 <= self.max_parallel_tasks <= 8 or not 1 <= self.max_tasks <= 512:
            raise ValueError("invalid_worker_capacity")
        if not 1 <= self.max_messages <= 1000 or not 1 <= self.max_context_fragments <= 256:
            raise ValueError("invalid_worker_metadata_capacity")
        if not 1000 <= self.max_context_chars <= 100_000 or not 1 <= self.default_timeout_seconds <= 3600:
            raise ValueError("invalid_worker_bounds")
        if not 0 <= self.max_fallbacks <= 4:
            raise ValueError("invalid_worker_fallback_limit")
        if not self.require_approval_for_writes or self.worktree_auto_merge:
            raise ValueError("unsafe_worker_authority_configuration")


def safe_metadata(values: Mapping[str, object]) -> dict[str, str]:
    return {
        bounded(key, 80): bounded(value, 300)
        for key, value in tuple(values.items())[:MAX_ITEMS]
        if not SECRET_PATTERN.search(f"{key}={value}")
    }


Artifact = WorkerArtifact


class PathLikeUnsafe:
    @staticmethod
    def is_unsafe(value: str) -> bool:
        if not value:
            return False
        normalized = value.replace("\\", "/")
        return normalized.startswith("/") or bool(re.match(r"^[A-Za-z]:/", normalized)) or ".." in normalized.split("/")
