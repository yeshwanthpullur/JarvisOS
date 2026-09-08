"""Atomic metadata-only checkpoints and bounded recovery planning."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
from threading import RLock

from .assurance_models import (
    FailureRecord,
    RecoveryAction,
    RecoveryDecision,
    RetryPolicy,
    RecoveryState,
    WorkCheckpoint,
)
from .models import SECRET_PATTERN, WorkerTaskStatus, now


class CheckpointStore:
    """Persists bounded references, never raw prompts, transcripts, or secrets."""

    SCHEMA_VERSION = 1

    def __init__(self, path: Path | None = None, *, max_checkpoints: int = 200) -> None:
        self.path = path
        self.max_checkpoints = max(1, min(max_checkpoints, 1000))
        self._items: dict[str, WorkCheckpoint] = {}
        self._side_effect_receipts: dict[str, str] = {}
        self._lock = RLock()
        if path and path.exists():
            self._load()

    @staticmethod
    def _safe_payload(payload: object) -> bool:
        serialized = json.dumps(payload, sort_keys=True, default=str)
        return len(serialized) <= 2_000_000 and not SECRET_PATTERN.search(serialized)

    def save(self, checkpoint: WorkCheckpoint) -> WorkCheckpoint:
        payload = asdict(checkpoint)
        if not self._safe_payload(payload):
            raise ValueError("unsafe_checkpoint_payload")
        with self._lock:
            current = self._items.get(checkpoint.checkpoint_id)
            if current and current.task_id != checkpoint.task_id:
                raise ValueError("checkpoint_identity_mismatch")
            self._items[checkpoint.checkpoint_id] = checkpoint
            while len(self._items) > self.max_checkpoints:
                oldest = min(self._items.values(), key=lambda item: item.updated_at)
                self._items.pop(oldest.checkpoint_id, None)
            self._flush()
        return checkpoint

    def update(self, checkpoint_id: str, **changes: object) -> WorkCheckpoint:
        with self._lock:
            current = self._items.get(checkpoint_id)
            if current is None:
                raise KeyError("checkpoint_not_found")
            allowed = {
                "status", "provider_ref", "model_ref", "dependency_refs",
                "workspace_ref", "context_refs", "output_refs", "artifact_refs",
                "evidence_refs", "message_refs", "approval_refs", "completed_stages",
                "pending_stage", "retry_count", "timeout_seconds", "idempotency_keys",
                "failure",
                "failure_history", "recovery_state", "resume_reference",
            }
            if set(changes) - allowed:
                raise ValueError("unsupported_checkpoint_update")
            updated = replace(current, **changes, updated_at=now())
            return self.save(updated)

    def latest(self, task_id: str) -> WorkCheckpoint | None:
        values = [item for item in self._items.values() if item.task_id == task_id]
        return max(values, key=lambda item: item.updated_at) if values else None

    def list(self, task_id: str | None = None) -> tuple[WorkCheckpoint, ...]:
        values = tuple(self._items.values())
        if task_id:
            values = tuple(item for item in values if item.task_id == task_id)
        return tuple(sorted(values, key=lambda item: item.updated_at, reverse=True))

    def record_side_effect(self, idempotency_key: str, evidence_ref: str) -> bool:
        """Return False when a completed side effect has already been recorded."""
        if not idempotency_key or len(idempotency_key) > 200 or SECRET_PATTERN.search(idempotency_key):
            raise ValueError("invalid_idempotency_key")
        with self._lock:
            if idempotency_key in self._side_effect_receipts:
                return False
            self._side_effect_receipts[idempotency_key] = evidence_ref[:300]
            self._flush()
            return True

    def side_effect_completed(self, idempotency_key: str) -> bool:
        return idempotency_key in self._side_effect_receipts

    def stale(self, *, now_value: datetime | None = None) -> tuple[WorkCheckpoint, ...]:
        current = now_value or datetime.now(UTC)
        output = []
        for item in self._items.values():
            if item.status not in {WorkerTaskStatus.RUNNING, WorkerTaskStatus.WAITING, WorkerTaskStatus.RETRYING}:
                continue
            try:
                updated = datetime.fromisoformat(item.updated_at)
            except ValueError:
                output.append(item)
                continue
            if (current - updated).total_seconds() > item.timeout_seconds:
                output.append(item)
        return tuple(output)

    def _flush(self) -> None:
        if self.path is None:
            return
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "authority": "jarvis_work_assurance",
            "checkpoints": [asdict(item) for item in self._items.values()],
            "side_effect_receipts": self._side_effect_receipts,
        }
        if not self._safe_payload(payload):
            raise ValueError("unsafe_checkpoint_payload")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(payload, sort_keys=True, default=str), encoding="utf-8")
        temporary.replace(self.path)

    def _load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8")) if self.path else {}
        except (OSError, ValueError) as exc:
            raise ValueError("invalid_checkpoint_store") from exc
        if payload.get("schema_version") != self.SCHEMA_VERSION or payload.get("authority") != "jarvis_work_assurance":
            raise ValueError("invalid_checkpoint_store")
        if not self._safe_payload(payload):
            raise ValueError("unsafe_checkpoint_store")
        try:
            for raw in tuple(payload.get("checkpoints", ()))[: self.max_checkpoints]:
                failure = raw.get("failure")
                raw["failure"] = FailureRecord(**failure) if failure else None
                raw["failure_history"] = tuple(FailureRecord(**item) for item in raw.get("failure_history", ()))
                raw["recovery_state"] = RecoveryState(raw.get("recovery_state", "clean"))
                raw["status"] = WorkerTaskStatus(raw["status"])
                for key in (
                    "dependency_refs", "context_refs", "output_refs", "artifact_refs",
                    "evidence_refs", "message_refs", "approval_refs", "completed_stages",
                    "idempotency_keys",
                ):
                    raw[key] = tuple(raw.get(key, ()))
                item = WorkCheckpoint(**raw)
                self._items[item.checkpoint_id] = item
            receipts = payload.get("side_effect_receipts", {})
            if not isinstance(receipts, dict):
                raise ValueError("invalid_receipts")
            self._side_effect_receipts = {str(key)[:200]: str(value)[:300] for key, value in tuple(receipts.items())[:1000]}
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("invalid_checkpoint_store") from exc

    def integrity(self) -> str:
        material = "|".join(f"{item.checkpoint_id}:{item.updated_at}" for item in self.list())
        return hashlib.sha256(material.encode("utf-8")).hexdigest()


class RecoveryPlanner:
    def __init__(self, policy: RetryPolicy | None = None) -> None:
        self.policy = policy or RetryPolicy()

    def classify(self, checkpoint: WorkCheckpoint) -> RecoveryDecision:
        failure = checkpoint.failure
        if checkpoint.status is WorkerTaskStatus.COMPLETED:
            return RecoveryDecision(checkpoint.checkpoint_id, RecoveryAction.NEEDS_REVIEW, "Completed work must be verified rather than replayed.", False)
        if checkpoint.approval_refs and checkpoint.pending_stage.startswith("side_effect"):
            return RecoveryDecision(checkpoint.checkpoint_id, RecoveryAction.NEEDS_USER_APPROVAL, "A pending side effect requires fresh approval and state validation.", False, True)
        if checkpoint.retry_count >= self.policy.max_attempts:
            return RecoveryDecision(checkpoint.checkpoint_id, RecoveryAction.IRRECOVERABLE, "The bounded retry budget is exhausted.", False)
        if failure is None:
            return RecoveryDecision(checkpoint.checkpoint_id, RecoveryAction.SAFE_RESUME, "Checkpoint has no recorded failure and completed stages will not be repeated.", True)
        failure_type = failure.failure_type.lower()
        if failure_type in {"provider_failure", "provider_unavailable"} and self.policy.allow_provider_reroute:
            return RecoveryDecision(checkpoint.checkpoint_id, RecoveryAction.REROUTE_PROVIDER, "Provider failure is eligible for one bounded compatible reroute.", True)
        if failure_type in {"worker_crash", "agent_crashed"}:
            action = RecoveryAction.RETRY_DIFFERENT_WORKER if self.policy.allow_different_worker else RecoveryAction.RETRY_SAME_WORKER
            return RecoveryDecision(checkpoint.checkpoint_id, action, "Worker failure is retryable without repeating completed stages.", True)
        if failure_type in {"timeout", "task_timeout", "interrupted"}:
            return RecoveryDecision(checkpoint.checkpoint_id, RecoveryAction.SAFE_RESUME, "Interrupted work can resume at the recorded pending stage.", True)
        if failure_type in {"validation", "review"}:
            return RecoveryDecision(checkpoint.checkpoint_id, RecoveryAction.REPLAN_TASK, "Failed validation requires an evidence-based rework plan.", False)
        if not failure.retryable:
            return RecoveryDecision(checkpoint.checkpoint_id, RecoveryAction.IRRECOVERABLE, "Failure is not marked retryable.", False)
        return RecoveryDecision(checkpoint.checkpoint_id, RecoveryAction.RETRY_SAME_WORKER, "Retryable failure may use the same worker within the configured budget.", True)

    def resume(self, checkpoint: WorkCheckpoint) -> WorkCheckpoint:
        decision = self.classify(checkpoint)
        if not decision.safe_to_resume:
            raise ValueError(f"resume_not_safe:{decision.action.value}")
        return replace(
            checkpoint,
            status=WorkerTaskStatus.RETRYING,
            recovery_state=RecoveryState.RESUMABLE,
            retry_count=checkpoint.retry_count + (1 if checkpoint.failure else 0),
            failure_history=checkpoint.failure_history + ((checkpoint.failure,) if checkpoint.failure else ()),
            failure=None,
            updated_at=now(),
        )
