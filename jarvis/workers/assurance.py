"""Review, verification, rework, evidence, and integration-candidate gates."""

from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path

from .assurance_models import (
    CandidateCheck,
    CandidateStatus,
    EvidenceRecord,
    EvidenceType,
    IntegrationCandidate,
    ReworkAttempt,
    ReworkDisposition,
    ReworkRequest,
    ReviewFinding,
    ReviewSeverity,
    ReviewVerdict,
    StructuredReview,
    VerificationCheck,
    VerificationPlan,
    VerificationResult,
    VerificationState,
)
from .models import SECRET_PATTERN, WorkerStatus, bounded
from .registry import WorkerRegistry


class EvidenceStore:
    SCHEMA_VERSION = 1

    def __init__(self, path: Path | None = None, *, max_items: int = 500) -> None:
        self.path = path
        self.max_items = max(1, min(max_items, 5000))
        self._items: dict[str, EvidenceRecord] = {}
        if path and path.exists():
            self._load()

    def add(self, evidence: EvidenceRecord) -> EvidenceRecord:
        serialized = json.dumps(asdict(evidence), default=str)
        if len(serialized) > 100_000 or SECRET_PATTERN.search(serialized):
            raise ValueError("unsafe_evidence")
        if evidence.evidence_id in self._items:
            raise ValueError("duplicate_evidence")
        self._items[evidence.evidence_id] = evidence
        while len(self._items) > self.max_items:
            first = next(iter(self._items))
            self._items.pop(first)
        self._flush()
        return evidence

    def get(self, evidence_id: str) -> EvidenceRecord | None:
        return self._items.get(evidence_id)

    def list(self, task_id: str | None = None) -> tuple[EvidenceRecord, ...]:
        values = tuple(self._items.values())
        return tuple(item for item in values if not task_id or item.task_id == task_id)

    def invalidate(self, evidence_id: str) -> EvidenceRecord:
        current = self._items[evidence_id]
        updated = replace(current, stale=True, validated=False)
        self._items[evidence_id] = updated
        self._flush()
        return updated

    def valid(self, evidence_id: str) -> bool:
        item = self.get(evidence_id)
        return bool(item and item.validated and not item.stale)

    def summary(self, task_id: str) -> dict[str, object]:
        values = self.list(task_id)
        return {
            "task_id": task_id,
            "evidence": len(values),
            "validated": sum(item.validated and not item.stale for item in values),
            "types": tuple(sorted({item.evidence_type.value for item in values}))[:20],
            "authoritative": False,
        }

    def _flush(self) -> None:
        if self.path is None:
            return
        payload = {"schema_version": self.SCHEMA_VERSION, "evidence": [asdict(item) for item in self._items.values()]}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True, default=str), encoding="utf-8")
        temporary.replace(self.path)

    def _load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8")) if self.path else {}
            if payload.get("schema_version") != self.SCHEMA_VERSION:
                raise ValueError
            for raw in tuple(payload.get("evidence", ()))[: self.max_items]:
                raw["evidence_type"] = EvidenceType(raw["evidence_type"])
                item = EvidenceRecord(**raw)
                self._items[item.evidence_id] = item
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid_evidence_store") from exc


class ReviewCoordinator:
    ROLES = ("correctness", "security", "architecture", "regression", "integration")

    def __init__(self, registry: WorkerRegistry) -> None:
        self.registry = registry

    def select_reviewer(self, implementer_id: str, *, role: str = "correctness") -> tuple[str, bool]:
        if role not in self.ROLES:
            raise ValueError("invalid_review_role")
        records = self.registry.list()
        candidates = [
            item for item in records
            if item.worker_id != implementer_id
            and item.detected
            and item.status in {WorkerStatus.READY, WorkerStatus.DEGRADED}
            and item.capabilities.independent_review
        ]
        if candidates:
            return sorted(candidates, key=lambda item: item.worker_id)[0].worker_id, True
        implementer = self.registry.get(implementer_id)
        if implementer and implementer.detected:
            return implementer_id, False
        raise ValueError("reviewer_unavailable")

    @staticmethod
    def validate(review: StructuredReview) -> bool:
        if review.verdict is ReviewVerdict.SECURITY_REJECTED and not any(
            item.severity is ReviewSeverity.CRITICAL for item in review.findings
        ):
            raise ValueError("security_rejection_requires_critical_finding")
        return True


class VerificationEngine:
    def plan(self, task_id: str, task_type: str, completion_criteria: tuple[str, ...] = ()) -> VerificationPlan:
        normalized = task_type.lower()
        checks: list[VerificationCheck] = []
        if normalized in {"coding", "code", "implementation"}:
            checks.extend((
                VerificationCheck("targeted_tests", "Targeted tests"),
                VerificationCheck("regression_tests", "Relevant regression tests"),
                VerificationCheck("structured_review", "Independent structured review"),
            ))
        elif normalized in {"documentation", "documents"}:
            checks.extend((
                VerificationCheck("documentation_consistency", "Documentation consistency"),
                VerificationCheck("reference_validation", "Reference validation"),
            ))
        elif normalized in {"configuration", "config"}:
            checks.extend((
                VerificationCheck("schema_validation", "Configuration schema validation"),
                VerificationCheck("targeted_tests", "Targeted tests"),
            ))
        else:
            checks.append(VerificationCheck("completion_criteria", "Completion criteria evidence"))
        for index, criterion in enumerate(completion_criteria[:16]):
            checks.append(VerificationCheck(f"criterion_{index + 1}", bounded(criterion, 200)))
        return VerificationPlan(task_id, tuple(checks))

    @staticmethod
    def evaluate(plan: VerificationPlan, evidence: EvidenceStore) -> VerificationResult:
        evaluated = []
        for check in plan.checks:
            valid_refs = tuple(ref for ref in check.evidence_refs if evidence.valid(ref))
            state = check.state
            if state is VerificationState.PASSED and not valid_refs:
                state = VerificationState.FAILED
            evaluated.append(replace(check, state=state, evidence_refs=valid_refs))
        required = tuple(item for item in evaluated if item.required)
        allowed = bool(required) and all(item.state is VerificationState.PASSED for item in required)
        state = VerificationState.PASSED if allowed else VerificationState.BLOCKED if any(item.state is VerificationState.BLOCKED for item in required) else VerificationState.FAILED
        return VerificationResult(plan.task_id, plan.plan_id, state, tuple(evaluated), allowed)


class ReworkEngine:
    def __init__(self, max_attempts: int = 2) -> None:
        self.max_attempts = max(1, min(max_attempts, 5))
        self.attempts: list[ReworkAttempt] = []

    def request(self, task_id: str, review: StructuredReview, attempt: int) -> ReworkRequest:
        if review.verdict is ReviewVerdict.SECURITY_REJECTED:
            return ReworkRequest(task_id, (review.review_id,), ("Stop; security policy rejected this candidate.",), attempt, self.max_attempts, True)
        if attempt > self.max_attempts:
            raise ValueError("rework_budget_exhausted")
        findings = tuple(item for item in review.findings if item.severity is not ReviewSeverity.NOTE)
        if not findings:
            raise ValueError("rework_requires_findings")
        return ReworkRequest(
            task_id,
            tuple(f"{review.review_id}:{index}" for index, _ in enumerate(findings, 1)),
            tuple(item.required_action or item.explanation for item in findings),
            attempt,
            self.max_attempts,
        )

    def finish(self, request: ReworkRequest, evidence_refs: tuple[str, ...], *, passed: bool) -> ReworkAttempt:
        if request.security_blocked:
            disposition = ReworkDisposition.SECURITY_BLOCKED
        elif passed:
            disposition = ReworkDisposition.COMPLETED
        elif request.attempt >= request.max_attempts:
            disposition = ReworkDisposition.RETRY_EXHAUSTED
        else:
            disposition = ReworkDisposition.REWORK_REQUIRED
        result = ReworkAttempt(request.request_id, request.task_id, request.attempt, disposition, evidence_refs[:32])
        self.attempts.append(result)
        return result


class IntegrationCandidateGate:
    PROTECTED = (".env", "installations/", "models/", "data/", "jarvis/voice_intelligence.py.backup")

    @classmethod
    def evaluate(
        cls,
        candidate: IntegrationCandidate,
        *,
        changed_files: tuple[str, ...],
        stale_base: bool = False,
        conflicts: bool = False,
    ) -> IntegrationCandidate:
        checks = list(candidate.checks)
        protected = tuple(
            path for path in changed_files
            if path.replace("\\", "/") in {".env", "jarvis/voice_intelligence.py.backup"}
            or any(path.replace("\\", "/").startswith(prefix) for prefix in ("installations/", "models/", "data/"))
        )
        checks.extend((
            CandidateCheck("clean_worktree", not conflicts, reason="unresolved_conflicts" if conflicts else ""),
            CandidateCheck("fresh_base", not stale_base, reason="stale_base" if stale_base else ""),
            CandidateCheck("protected_files", not protected, reason="protected_file_change" if protected else ""),
        ))
        required_pass = all(item.passed or not item.required for item in checks)
        status = CandidateStatus.STALE if stale_base else CandidateStatus.REJECTED if not required_pass else CandidateStatus.READY
        return replace(candidate, checks=tuple(checks), status=status, automatic_merge=False)


def evidence_integrity(summary: str, safe_reference: str) -> str:
    return hashlib.sha256(f"{summary}|{safe_reference}".encode("utf-8")).hexdigest()


class WorkAssuranceRuntime:
    """Composes durable recovery and evidence gates without executing work."""

    def __init__(self, root: Path, registry: WorkerRegistry) -> None:
        from .checkpoints import CheckpointStore, RecoveryPlanner

        state_root = root / "data" / "workers" / "assurance"
        self.checkpoints = CheckpointStore(state_root / "checkpoints.json")
        self.recovery = RecoveryPlanner()
        self.evidence = EvidenceStore(state_root / "evidence.json")
        self.reviews = ReviewCoordinator(registry)
        self.verification = VerificationEngine()
        self.rework = ReworkEngine()
        self.candidates = IntegrationCandidateGate()

    def status(self) -> dict[str, object]:
        return {
            "status": "ready",
            "authority": "verify_and_recommend_only",
            "checkpoints": len(self.checkpoints.list()),
            "evidence": len(self.evidence.list()),
            "automatic_merge": False,
            "side_effect_replay": False,
        }
