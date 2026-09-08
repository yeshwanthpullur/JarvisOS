"""Typed records for durable work recovery and evidence-based completion."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Mapping
from uuid import uuid4

from .models import WorkerTaskStatus, bounded, bounded_items, now, safe_metadata


class RecoveryAction(StrEnum):
    SAFE_RESUME = "safe_resume"
    RETRY_SAME_WORKER = "retry_same_worker"
    RETRY_DIFFERENT_WORKER = "retry_different_worker"
    REROUTE_PROVIDER = "reroute_provider"
    REPLAN_TASK = "replan_task"
    NEEDS_REVIEW = "needs_review"
    NEEDS_USER_APPROVAL = "needs_user_approval"
    IRRECOVERABLE = "irrecoverable"


class RecoveryState(StrEnum):
    CLEAN = "clean"
    INTERRUPTED = "interrupted"
    FAILED = "failed"
    RESUMABLE = "resumable"
    APPROVAL_PENDING = "approval_pending"
    EXHAUSTED = "exhausted"
    IRRECOVERABLE = "irrecoverable"


class ReviewVerdict(StrEnum):
    PASS = "pass"
    PASS_WITH_NOTES = "pass_with_notes"
    REWORK_REQUIRED = "rework_required"
    BLOCKED = "blocked"
    SECURITY_REJECTED = "security_rejected"


class ReviewSeverity(StrEnum):
    NOTE = "note"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class VerificationState(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED_WITH_REASON = "skipped_with_reason"


class EvidenceType(StrEnum):
    TEST_RESULT = "test_result"
    REVIEW_RESULT = "review_result"
    DIFF = "diff"
    ARTIFACT = "artifact"
    COMMAND_RESULT = "command_result"
    STATIC_CHECK = "static_check"
    RUNTIME_CHECK = "runtime_check"
    SCREENSHOT_REFERENCE = "screenshot_reference"
    SOURCE_REFERENCE = "source_reference"
    BUILD_RESULT = "build_result"
    HEALTH_CHECK = "health_check"
    CHECKPOINT = "checkpoint"
    USER_APPROVAL = "user_approval"
    RESEARCH_SOURCE = "research_source"
    CRAWL_RESULT = "crawl_result"
    DOCUMENT_PARSE = "document_parse"
    OCR_RESULT = "ocr_result"
    CITATION = "citation"
    GROUNDING_CHECK = "grounding_check"
    EXTRACTION_CHECK = "extraction_check"
    KNOWLEDGE_INGESTION = "knowledge_ingestion"
    VECTOR_UPSERT = "vector_upsert"
    RETRIEVAL_RESULT = "retrieval_result"
    GROUNDING_RESULT = "grounding_result"
    MEMORY_WRITE = "memory_write"
    MEMORY_UPDATE = "memory_update"
    MEMORY_DELETE = "memory_delete"
    MEMORY_EXPIRY = "memory_expiry"
    INDEX_HEALTH = "index_health"
    EMBEDDING_RESULT = "embedding_result"
    RERANK_RESULT = "rerank_result"
    MEMORY_MUTATION = "memory_mutation"
    STT_TEST = "stt_test"
    TTS_TEST = "tts_test"
    VOICE_SESSION_TEST = "voice_session_test"
    STT_HEALTH = "stt_health"
    TTS_HEALTH = "tts_health"
    VOICE_ROUTE = "voice_route"
    PTT_STATE_TEST = "ptt_state_test"
    FALLBACK_TEST = "fallback_test"


class ReworkDisposition(StrEnum):
    COMPLETED = "completed"
    REWORK_REQUIRED = "rework_required"
    RETRY_EXHAUSTED = "retry_exhausted"
    BLOCKED = "blocked"
    NEEDS_USER = "needs_user"
    SECURITY_BLOCKED = "security_blocked"


class CandidateStatus(StrEnum):
    DRAFT = "draft"
    TESTING = "testing"
    REVIEWING = "reviewing"
    REWORK = "rework"
    READY = "ready"
    REJECTED = "rejected"
    STALE = "stale"
    MERGED = "merged"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 2
    allow_different_worker: bool = True
    allow_provider_reroute: bool = True
    retry_side_effects: bool = False

    def __post_init__(self) -> None:
        if not 0 <= self.max_attempts <= 5 or self.retry_side_effects:
            raise ValueError("unsafe_retry_policy")


@dataclass(frozen=True, slots=True)
class RunAttempt:
    task_id: str
    run_id: str
    worker_id: str
    attempt: int
    status: WorkerTaskStatus
    provider_ref: str = ""
    model_ref: str = ""
    started_at: str = field(default_factory=now)
    finished_at: str = ""

    def __post_init__(self) -> None:
        if not 1 <= self.attempt <= 6:
            raise ValueError("invalid_run_attempt")


@dataclass(frozen=True, slots=True)
class FailureRecord:
    task_id: str
    run_id: str
    failure_type: str
    stage: str
    retryable: bool
    message: str
    occurred_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "message", bounded(self.message, 500))


@dataclass(frozen=True, slots=True)
class WorkCheckpoint:
    goal_id: str
    project_id: str
    task_id: str
    run_id: str
    worker_id: str
    status: WorkerTaskStatus
    checkpoint_id: str = field(default_factory=lambda: f"checkpoint-{uuid4().hex[:12]}")
    provider_ref: str = ""
    model_ref: str = ""
    dependency_refs: tuple[str, ...] = ()
    workspace_ref: str = ""
    context_refs: tuple[str, ...] = ()
    output_refs: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    message_refs: tuple[str, ...] = ()
    approval_refs: tuple[str, ...] = ()
    completed_stages: tuple[str, ...] = ()
    pending_stage: str = ""
    retry_count: int = 0
    timeout_seconds: int = 180
    idempotency_keys: tuple[str, ...] = ()
    failure: FailureRecord | None = None
    failure_history: tuple[FailureRecord, ...] = ()
    recovery_state: RecoveryState = RecoveryState.CLEAN
    resume_reference: str = ""
    created_at: str = field(default_factory=now)
    updated_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not all((self.task_id, self.run_id, self.worker_id)):
            raise ValueError("checkpoint_identity_required")
        collections = (
            self.dependency_refs, self.context_refs, self.output_refs,
            self.artifact_refs, self.evidence_refs, self.message_refs,
            self.approval_refs, self.completed_stages, self.idempotency_keys,
        )
        if any(len(items) > 64 for items in collections) or len(self.failure_history) > 16:
            raise ValueError("checkpoint_item_limit_exceeded")
        if not 0 <= self.retry_count <= 5 or not 1 <= self.timeout_seconds <= 86_400:
            raise ValueError("checkpoint_bounds_invalid")


@dataclass(frozen=True, slots=True)
class RecoveryDecision:
    checkpoint_id: str
    action: RecoveryAction
    reason: str
    safe_to_resume: bool
    requires_approval: bool = False
    next_worker_id: str = ""
    next_provider_ref: str = ""
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason", bounded(self.reason, 500))
        object.__setattr__(self, "warnings", bounded_items(self.warnings))


@dataclass(frozen=True, slots=True)
class ReviewFinding:
    category: str
    severity: ReviewSeverity
    explanation: str
    required_action: str = ""
    safe_file_ref: str = ""
    location_ref: str = ""
    evidence_refs: tuple[str, ...] = ()
    confidence: float = 0.5

    def __post_init__(self) -> None:
        if not self.explanation.strip() or not 0 <= self.confidence <= 1:
            raise ValueError("invalid_review_finding")
        object.__setattr__(self, "explanation", bounded(self.explanation, 800))
        object.__setattr__(self, "required_action", bounded(self.required_action, 500))


@dataclass(frozen=True, slots=True)
class StructuredReview:
    task_id: str
    reviewer_id: str
    role: str
    verdict: ReviewVerdict
    findings: tuple[ReviewFinding, ...] = ()
    independent: bool = True
    trusted: bool = False
    review_id: str = field(default_factory=lambda: f"review-{uuid4().hex[:12]}")
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.task_id or not self.reviewer_id or len(self.findings) > 32:
            raise ValueError("invalid_structured_review")
        blocking = any(item.severity in {ReviewSeverity.HIGH, ReviewSeverity.CRITICAL} for item in self.findings)
        if blocking and self.verdict in {ReviewVerdict.PASS, ReviewVerdict.PASS_WITH_NOTES}:
            raise ValueError("blocking_finding_requires_blocking_verdict")


@dataclass(frozen=True, slots=True)
class VerificationCheck:
    check_id: str
    name: str
    required: bool = True
    state: VerificationState = VerificationState.PENDING
    evidence_refs: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class VerificationPlan:
    task_id: str
    checks: tuple[VerificationCheck, ...]
    plan_id: str = field(default_factory=lambda: f"verify-{uuid4().hex[:12]}")
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not self.task_id or not self.checks or len(self.checks) > 32:
            raise ValueError("invalid_verification_plan")
        if len({item.check_id for item in self.checks}) != len(self.checks):
            raise ValueError("duplicate_verification_check")


@dataclass(frozen=True, slots=True)
class VerificationResult:
    task_id: str
    plan_id: str
    state: VerificationState
    checks: tuple[VerificationCheck, ...]
    completion_allowed: bool
    warnings: tuple[str, ...] = ()
    completed_at: str = field(default_factory=now)


@dataclass(frozen=True, slots=True)
class EvidenceRecord:
    task_id: str
    run_id: str
    evidence_type: EvidenceType
    source: str
    summary: str
    safe_reference: str
    validated: bool = False
    trusted: bool = False
    stale: bool = False
    integrity: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)
    evidence_id: str = field(default_factory=lambda: f"evidence-{uuid4().hex[:12]}")
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if not all((self.task_id, self.run_id, self.source, self.summary)):
            raise ValueError("invalid_evidence")
        object.__setattr__(self, "summary", bounded(self.summary, 1000))
        object.__setattr__(self, "safe_reference", bounded(self.safe_reference, 300))
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))
        if self.integrity and len(self.integrity) != 64:
            raise ValueError("invalid_evidence_integrity")


@dataclass(frozen=True, slots=True)
class ReworkRequest:
    task_id: str
    finding_refs: tuple[str, ...]
    instructions: tuple[str, ...]
    attempt: int
    max_attempts: int
    security_blocked: bool = False
    request_id: str = field(default_factory=lambda: f"rework-{uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        if not self.finding_refs or not self.instructions:
            raise ValueError("evidence_based_rework_required")
        if not 1 <= self.attempt <= self.max_attempts <= 5:
            raise ValueError("invalid_rework_budget")


@dataclass(frozen=True, slots=True)
class ReworkAttempt:
    request_id: str
    task_id: str
    attempt: int
    disposition: ReworkDisposition
    correction_evidence_refs: tuple[str, ...] = ()
    completed_at: str = field(default_factory=now)


@dataclass(frozen=True, slots=True)
class CandidateCheck:
    name: str
    passed: bool
    required: bool = True
    evidence_ref: str = ""
    reason: str = ""


@dataclass(frozen=True, slots=True)
class IntegrationCandidate:
    task_id: str
    branch_ref: str
    workspace_ref: str
    artifact_refs: tuple[str, ...]
    checks: tuple[CandidateCheck, ...]
    candidate_id: str = field(default_factory=lambda: f"candidate-{uuid4().hex[:12]}")
    status: CandidateStatus = CandidateStatus.DRAFT
    base_revision: str = ""
    automatic_merge: bool = False
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        if self.automatic_merge:
            raise ValueError("automatic_merge_forbidden")
        if len(self.artifact_refs) > 64 or len(self.checks) > 32:
            raise ValueError("candidate_item_limit_exceeded")
