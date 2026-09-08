"""Bounded read models and policy-controlled actions for the local control room."""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, field, replace
from enum import StrEnum
from typing import Any
from uuid import uuid4

from jarvis.workers.assurance_models import CandidateStatus
from jarvis.workers.models import WorkerTaskStatus, bounded, now
from jarvis.workers.runtime import WorkerRuntime


class ControlRoomAction(StrEnum):
    PAUSE_TASK = "pause_task"
    RESUME_TASK = "resume_task"
    CANCEL_TASK = "cancel_task"
    REQUEST_RETRY = "request_retry"
    APPROVE_STEP = "approve_step"
    REJECT_CANDIDATE = "reject_candidate"
    INSPECT_EVIDENCE = "inspect_evidence"


@dataclass(frozen=True, slots=True)
class ControlRoomEvent:
    event_type: str
    summary: str
    status: str
    task_id: str = ""
    safe_reference: str = ""
    event_id: str = field(default_factory=lambda: f"event-{uuid4().hex[:12]}")
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "summary", bounded(self.summary, 300))


class ControlRoomRuntime:
    """Read-oriented facade; actions call Jarvis-owned transitions only."""

    def __init__(self, workers: WorkerRuntime, *, max_events: int = 200) -> None:
        self.workers = workers
        self.events: deque[ControlRoomEvent] = deque(maxlen=max(20, min(max_events, 1000)))
        self.candidates: dict[str, Any] = {}
        self.subsystem_status: dict[str, Any] = {}

    def bounded_subsystem_status(self) -> dict[str, object]:
        output = {}
        for name, provider in tuple(self.subsystem_status.items())[:20]:
            try: output[name] = provider()
            except Exception: output[name] = {"status": "unavailable"}
        return output

    def emit(self, event_type: str, summary: str, status: str, *, task_id: str = "", safe_reference: str = "") -> ControlRoomEvent:
        event = ControlRoomEvent(event_type, summary, status, task_id, safe_reference)
        self.events.append(event)
        return event

    def snapshot(self, *, offset: int = 0, limit: int = 50) -> dict[str, object]:
        limit = max(1, min(limit, 100))
        work = self.workers.work
        tasks = sorted(work.tasks.values(), key=lambda item: item.task_id)
        workers = self.workers.registry.list()
        checkpoints = self.workers.assurance.checkpoints.list()
        evidence = self.workers.assurance.evidence.list()
        events = tuple(self.events)[-limit:]
        return {
            "status": "ready",
            "authority": "jarvis_native_read_and_policy_actions",
            "overview": {
                "goals": len(work.goals), "tasks": len(tasks),
                "active": sum(item.status is WorkerTaskStatus.RUNNING for item in tasks),
                "blocked": sum(item.status is WorkerTaskStatus.BLOCKED for item in tasks),
                "pending_approvals": sum(item.state == "required" for item in work.approvals.values()),
                "workers": len(workers),
            },
            "goals": [{"goal_id": item.goal_id, "title": bounded(item.title, 160), "status": item.status} for item in tuple(work.goals.values())[offset:offset + limit]],
            "tasks": [{"task_id": item.task_id, "title": bounded(item.title, 180), "owner": item.owner_worker_id, "status": item.status.value, "dependencies": item.dependencies, "risk": item.risk} for item in tasks[offset:offset + limit]],
            "dag": [{"task_id": item.task_id, "dependencies": item.dependencies, "status": item.status.value} for item in tasks[offset:offset + limit]],
            "workers": [{"worker_id": item.worker_id, "name": item.display_name, "status": item.status.value, "health": item.health_reason, "capabilities": item.capabilities.supported_task_types[:12], "execution": item.execution_enabled} for item in workers[:limit]],
            "runs": [asdict(item) for item in tuple(work.runs.values())[offset:offset + limit]],
            "checkpoints": [{"checkpoint_id": item.checkpoint_id, "task_id": item.task_id, "status": item.status.value, "pending_stage": item.pending_stage, "retry_count": item.retry_count, "updated_at": item.updated_at} for item in checkpoints[offset:offset + limit]],
            "messages": [{"message_id": item.message_id, "task_id": item.task_id, "sender": item.sender, "receiver": item.receiver, "kind": item.kind.value, "trust": item.trust, "created_at": item.created_at} for item in work.messages[-limit:]],
            "reviews": [asdict(item) for item in tuple(work.reviews.values())[offset:offset + limit]],
            "evidence": [{"evidence_id": item.evidence_id, "task_id": item.task_id, "type": item.evidence_type.value, "summary": item.summary, "validated": item.validated, "trusted": item.trusted, "stale": item.stale} for item in evidence[offset:offset + limit]],
            "candidates": [{"candidate_id": item.candidate_id, "task_id": item.task_id, "status": item.status.value, "automatic_merge": False} for item in tuple(self.candidates.values())[offset:offset + limit]],
            "approvals": [asdict(item) for item in tuple(work.approvals.values())[offset:offset + limit]],
            "providers": [{"provider_id": item.provider_id, "status": item.status, "local": item.locality == "local", "privacy": item.privacy_class} for item in self.workers.providers.list()[:limit]],
            "models": [{"model_id": item.model_id, "provider_id": item.provider_id, "status": item.status.value} for item in self.workers.models.list_models()[:limit]],
            "activity": [asdict(item) for item in events],
            "subsystems": self.bounded_subsystem_status(),
            "security": {"shell": False, "automatic_merge": False, "approval_bypass": False, "secrets_exposed": False},
        }

    def action(self, action: str, *, task_id: str = "", evidence_id: str = "", candidate_id: str = "", approval_ref: str = "") -> dict[str, object]:
        try:
            operation = ControlRoomAction(action)
        except ValueError as exc:
            raise ValueError("unsupported_control_room_action") from exc
        task = self.workers.work.tasks.get(task_id) if task_id else None
        if operation is ControlRoomAction.INSPECT_EVIDENCE:
            record = self.workers.assurance.evidence.get(evidence_id)
            if record is None:
                raise ValueError("unknown_evidence")
            self.emit("EvidenceInspected", "Bounded evidence metadata inspected.", "completed", task_id=record.task_id, safe_reference=record.evidence_id)
            return {"status": "completed", "evidence": {"evidence_id": record.evidence_id, "type": record.evidence_type.value, "summary": record.summary, "validated": record.validated, "stale": record.stale}}
        if operation is ControlRoomAction.REJECT_CANDIDATE:
            candidate = self.candidates.get(candidate_id)
            if candidate is None:
                raise ValueError("unknown_candidate")
            self.candidates[candidate_id] = replace(candidate, status=CandidateStatus.REJECTED, automatic_merge=False)
            self.emit("CandidateRejected", "Integration candidate rejected without merge.", "rejected", task_id=candidate.task_id, safe_reference=candidate_id)
            return {"status": "rejected", "candidate_id": candidate_id, "automatic_merge": False}
        if task is None:
            raise ValueError("unknown_task")
        if operation is ControlRoomAction.PAUSE_TASK:
            if task.status is not WorkerTaskStatus.RUNNING:
                raise ValueError("task_not_running")
            self.workers.work.mark(task_id, WorkerTaskStatus.WAITING)
            event_type, status = "TaskPaused", "waiting"
        elif operation is ControlRoomAction.RESUME_TASK:
            if task.status is WorkerTaskStatus.WAITING:
                self.workers.work.mark(task_id, WorkerTaskStatus.RUNNING)
            elif not self.workers.work.resume(task_id):
                raise ValueError("task_not_resumable")
            event_type, status = "TaskResumed", "running"
        elif operation is ControlRoomAction.CANCEL_TASK:
            if not self.workers.work.cancel(task_id):
                raise ValueError("task_not_cancellable")
            event_type, status = "TaskCancelled", "cancelled"
        elif operation is ControlRoomAction.REQUEST_RETRY:
            if not self.workers.work.request_retry(task_id):
                raise ValueError("retry_not_available")
            event_type, status = "ReworkStarted", "retrying"
        else:
            approval = next((item for item in self.workers.work.approvals.values() if item.task_ref == task_id and item.approval_ref == approval_ref and item.state == "required"), None)
            if approval is None:
                raise ValueError("authorization_required")
            self.workers.work.approvals[approval_ref] = replace(approval, state="granted")
            event_type, status = "ApprovalGranted", "granted"
        self.emit(event_type, f"{operation.value} accepted by Jarvis policy control.", status, task_id=task_id)
        return {"status": status, "task_id": task_id, "action": operation.value, "execution_started": False}
