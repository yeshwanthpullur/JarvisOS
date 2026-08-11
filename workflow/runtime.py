"""Bounded long-running workflow coordination and checkpoint runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
import json
import re
from typing import Any, Callable
from uuid import uuid4


MAX_TEXT = 1000
SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*\S+")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:12]}"


def _safe_text(value: object, limit: int = MAX_TEXT) -> str:
    text = SECRET_PATTERN.sub(r"\1=[REDACTED]", str(value)).replace("\\", "/")
    if re.search(r"^[A-Za-z]:/", text):
        text = text.rsplit("/", 1)[-1]
    return text[:limit]


def _safe_map(value: dict[str, Any], limit: int = 20) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in list(value.items())[:limit]:
        name = _safe_text(key, 80)
        if any(term in name.lower() for term in ("secret", "token", "password", "credential", "api_key")):
            continue
        if isinstance(item, (str, int, float, bool)) or item is None:
            result[name] = _safe_text(item, 300) if isinstance(item, str) else item
        elif isinstance(item, (list, tuple)):
            result[name] = tuple(_safe_text(entry, 160) for entry in item[:20])
        else:
            result[name] = _safe_text(type(item).__name__, 80)
    return result


class WorkflowRuntimeState(StrEnum):
    CREATED = "created"
    PLANNED = "planned"
    APPROVED = "approved"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING = "waiting"
    CHECKPOINTING = "checkpointing"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL_SUCCESS = "partial_success"
    TIMED_OUT = "timed_out"


class WorkflowStepState(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"
    ROLLED_BACK = "rolled_back"


class WorkflowDependencyType(StrEnum):
    HARD = "hard"
    SOFT = "soft"
    OPTIONAL = "optional"
    PARALLEL = "parallel"
    FALLBACK = "fallback"
    APPROVAL = "approval"
    PROVIDER = "provider"
    POLICY = "policy"


class WorkflowExecutionMode(StrEnum):
    INTERACTIVE = "interactive"
    ASSISTED = "assisted"
    BACKGROUND = "background"
    SCHEDULED = "scheduled"
    RECOVERY = "recovery"
    SIMULATION = "simulation"


@dataclass(frozen=True, slots=True)
class WorkflowLimits:
    max_active: int = 4
    max_parallel_steps: int = 2
    max_pending: int = 25
    default_timeout_seconds: int = 300
    max_retry_count: int = 2
    default_checkpoint_interval: int = 1
    max_event_history: int = 200
    max_checkpoint_history: int = 50
    max_artifacts: int = 50
    max_runtime_hours: int = 4

    def __post_init__(self) -> None:
        values = asdict(self)
        if any(not isinstance(value, int) or value < 1 for value in values.values()):
            raise ValueError("workflow_limits_must_be_positive")
        if self.max_parallel_steps > self.max_active:
            raise ValueError("workflow_parallel_limit_exceeds_active_limit")
        if self.max_retry_count > 5:
            raise ValueError("workflow_retry_limit_too_large")


@dataclass(frozen=True, slots=True)
class WorkflowDependency:
    step_id: str
    dependency_type: WorkflowDependencyType = WorkflowDependencyType.HARD


@dataclass(slots=True)
class RuntimeWorkflowStep:
    step_id: str
    step_type: str
    owner_agent: str = "prime"
    dependencies: tuple[WorkflowDependency, ...] = ()
    status: WorkflowStepState = WorkflowStepState.PENDING
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    checkpoint_required: bool = True
    maximum_retries: int = 0
    timeout_seconds: int = 60
    estimated_cost: float = 0.0
    estimated_duration_seconds: int = 0
    privacy_scope: str = "local_private"
    approval_required: bool = False
    broker_required: bool = False
    retries: int = 0
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        self.step_id = _safe_text(self.step_id, 100)
        self.step_type = _safe_text(self.step_type, 100)
        self.owner_agent = _safe_text(self.owner_agent, 100)
        self.inputs = _safe_map(self.inputs)
        self.outputs = _safe_map(self.outputs)
        if not self.step_id or self.timeout_seconds < 1 or self.maximum_retries < 0:
            raise ValueError("invalid_workflow_step")


@dataclass(slots=True)
class WorkflowRecordRuntime:
    workflow_id: str
    workflow_type: str
    initiating_request: str
    steps: tuple[RuntimeWorkflowStep, ...]
    workflow_version: str = "1.0"
    schema_version: str = "1.0"
    owner: str = "prime"
    state: WorkflowRuntimeState = WorkflowRuntimeState.CREATED
    priority: int = 5
    privacy_scope: str = "local_private"
    execution_policy: str = "policy_required"
    approval_state: str = "not_required"
    mode: WorkflowExecutionMode = WorkflowExecutionMode.INTERACTIVE
    resource_budget: dict[str, float] = field(default_factory=lambda: {"wall_seconds": 300.0, "provider_calls": 10.0})
    resource_used: dict[str, float] = field(default_factory=dict)
    checkpoint_interval: int = 1
    current_step: str | None = None
    completed_steps: list[str] = field(default_factory=list)
    failed_steps: list[str] = field(default_factory=list)
    cancelled_steps: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    started_at: str | None = None
    completed_at: str | None = None

    def __post_init__(self) -> None:
        self.workflow_id = _safe_text(self.workflow_id, 100)
        self.initiating_request = _safe_text(self.initiating_request, 500)
        self.resource_budget = {k: max(0.0, float(v)) for k, v in list(self.resource_budget.items())[:20]}
        if not self.workflow_id or not self.steps or len(self.steps) > 100:
            raise ValueError("invalid_workflow")


@dataclass(frozen=True, slots=True)
class RuntimeCheckpoint:
    checkpoint_id: str
    workflow_id: str
    workflow_version: str
    schema_version: str
    step_index: int
    created_at: str
    context_reference: str
    resource_state: dict[str, float]
    completed_steps: tuple[str, ...]
    remaining_steps: tuple[str, ...]
    interrupted_step: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WorkflowArtifact:
    artifact_id: str
    workflow_id: str
    owner: str
    artifact_type: str
    privacy_scope: str
    provenance: tuple[str, ...]
    retention_policy: str
    storage_class: str
    summary: str
    created_at: str = field(default_factory=_now)


@dataclass(frozen=True, slots=True)
class WorkflowEvent:
    event_id: str
    workflow_id: str
    event_type: str
    sequence: int
    timestamp: str
    component: str
    result: str
    policy_decision: str = "not_applicable"
    resource_summary: tuple[str, ...] = ()


class WorkflowRuntime:
    """Coordinates bounded workflows but never grants execution authority."""

    def __init__(self, limits: WorkflowLimits | None = None) -> None:
        self.limits = limits or WorkflowLimits()
        self.workflows: dict[str, WorkflowRecordRuntime] = {}
        self.checkpoints: dict[str, RuntimeCheckpoint] = {}
        self.artifacts: dict[str, WorkflowArtifact] = {}
        self.events: list[WorkflowEvent] = []
        self.metrics = {name: 0 for name in ("created", "running", "completed", "failed", "paused", "recovered", "retries", "timeouts", "parallel_executions")}

    def create(self, request: str, steps: tuple[RuntimeWorkflowStep, ...], *, workflow_type: str = "sequential", mode: WorkflowExecutionMode = WorkflowExecutionMode.INTERACTIVE, workflow_id: str | None = None) -> WorkflowRecordRuntime:
        active = sum(item.state in {WorkflowRuntimeState.RUNNING, WorkflowRuntimeState.PAUSED, WorkflowRuntimeState.WAITING} for item in self.workflows.values())
        pending = sum(item.state in {WorkflowRuntimeState.CREATED, WorkflowRuntimeState.PLANNED} for item in self.workflows.values())
        if active >= self.limits.max_active or pending >= self.limits.max_pending:
            raise ValueError("workflow_capacity_reached")
        record = WorkflowRecordRuntime(workflow_id or _id("wf"), workflow_type, request, steps, mode=mode)
        self.validate(record)
        record.state = WorkflowRuntimeState.PLANNED
        self.workflows[record.workflow_id] = record
        self.metrics["created"] += 1
        self._event(record.workflow_id, "workflow_created", "workflow_runtime", "planned")
        return record

    def validate(self, workflow: WorkflowRecordRuntime) -> None:
        identifiers = [step.step_id for step in workflow.steps]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("duplicate_workflow_step")
        known = set(identifiers)
        graph = {step.step_id: {dependency.step_id for dependency in step.dependencies if dependency.dependency_type is WorkflowDependencyType.HARD} for step in workflow.steps}
        if any(dependency not in known for dependencies in graph.values() for dependency in dependencies):
            raise ValueError("unknown_workflow_dependency")
        visiting: set[str] = set()
        visited: set[str] = set()
        def visit(node: str) -> None:
            if node in visiting:
                raise ValueError("workflow_dependency_cycle")
            if node in visited:
                return
            visiting.add(node)
            for dependency in graph[node]:
                visit(dependency)
            visiting.remove(node)
            visited.add(node)
        for node in graph:
            visit(node)

    def graph(self, workflow_id: str) -> dict[str, Any]:
        workflow = self.require(workflow_id)
        return {"workflow_id": workflow.workflow_id, "nodes": tuple(step.step_id for step in workflow.steps), "edges": tuple((dependency.step_id, step.step_id, dependency.dependency_type.value) for step in workflow.steps for dependency in step.dependencies)}

    def simulate(self, request: str = "simulation") -> dict[str, Any]:
        return {"mode": "simulation", "request": _safe_text(request, 200), "side_effects": False, "authority": "policy/approval/broker required", "limits": asdict(self.limits)}

    def start(self, workflow_id: str) -> WorkflowRecordRuntime:
        workflow = self.require(workflow_id)
        if workflow.mode in {WorkflowExecutionMode.BACKGROUND, WorkflowExecutionMode.SCHEDULED}:
            raise ValueError("unrestricted_background_execution_disabled")
        if workflow.state not in {WorkflowRuntimeState.PLANNED, WorkflowRuntimeState.APPROVED, WorkflowRuntimeState.PAUSED, WorkflowRuntimeState.RECOVERING}:
            raise ValueError("workflow_not_startable")
        workflow.state = WorkflowRuntimeState.RUNNING
        workflow.started_at = workflow.started_at or _now()
        workflow.updated_at = _now()
        self.metrics["running"] += 1
        self._event(workflow_id, "workflow_started", "workflow_runtime", "running")
        return workflow

    def ready_steps(self, workflow_id: str) -> tuple[RuntimeWorkflowStep, ...]:
        workflow = self.require(workflow_id)
        complete = set(workflow.completed_steps)
        ready: list[RuntimeWorkflowStep] = []
        for step in workflow.steps:
            if step.status is not WorkflowStepState.PENDING:
                continue
            hard = {item.step_id for item in step.dependencies if item.dependency_type in {WorkflowDependencyType.HARD, WorkflowDependencyType.APPROVAL, WorkflowDependencyType.POLICY}}
            if hard <= complete:
                ready.append(step)
        return tuple(ready[: self.limits.max_parallel_steps])

    def run_step(self, workflow_id: str, step_id: str, *, broker: Callable[[RuntimeWorkflowStep], dict[str, Any]] | None = None, approved: bool = False, elapsed_seconds: float = 0.0) -> RuntimeWorkflowStep:
        workflow = self.require(workflow_id)
        if workflow.state is not WorkflowRuntimeState.RUNNING:
            raise ValueError("workflow_not_running")
        step = self._step(workflow, step_id)
        if step not in self.ready_steps(workflow_id):
            raise ValueError("workflow_step_not_ready")
        if elapsed_seconds > step.timeout_seconds:
            step.status = WorkflowStepState.FAILED
            workflow.state = WorkflowRuntimeState.TIMED_OUT
            workflow.failed_steps.append(step_id)
            self.metrics["timeouts"] += 1
            self.checkpoint(workflow_id, interrupted_step=step_id)
            self._event(workflow_id, "workflow_timeout", step.owner_agent, "timed_out")
            return step
        if (step.approval_required and not approved) or (step.broker_required and broker is None):
            step.status = WorkflowStepState.BLOCKED
            workflow.state = WorkflowRuntimeState.WAITING
            self.checkpoint(workflow_id, interrupted_step=step_id)
            self._event(workflow_id, "step_blocked", step.owner_agent, "approval_or_broker_required", "denied")
            return step
        step.status = WorkflowStepState.RUNNING
        workflow.current_step = step_id
        self._event(workflow_id, "step_started", step.owner_agent, "running")
        try:
            result = broker(step) if broker is not None else {"status": "coordinated", "side_effects": False}
            step.outputs = _safe_map(result)
            if result.get("status") in {"blocked", "failed", "unavailable"}:
                raise RuntimeError(_safe_text(result.get("error", result["status"]), 160))
            step.status = WorkflowStepState.COMPLETED
            workflow.completed_steps.append(step_id)
            workflow.resource_used["wall_seconds"] = workflow.resource_used.get("wall_seconds", 0.0) + max(0.0, elapsed_seconds)
            self._event(workflow_id, "step_completed", step.owner_agent, "completed")
            if step.checkpoint_required or len(workflow.completed_steps) % workflow.checkpoint_interval == 0:
                self.checkpoint(workflow_id)
            if len(workflow.completed_steps) == len(workflow.steps):
                workflow.state = WorkflowRuntimeState.COMPLETED
                workflow.completed_at = _now()
                self.metrics["completed"] += 1
                self._event(workflow_id, "workflow_completed", "workflow_runtime", "completed")
        except Exception as exc:
            if step.retries < min(step.maximum_retries, self.limits.max_retry_count):
                step.retries += 1
                step.status = WorkflowStepState.PENDING
                self.metrics["retries"] += 1
                self._event(workflow_id, "step_retry_scheduled", step.owner_agent, "retry")
            else:
                step.status = WorkflowStepState.FAILED
                workflow.failed_steps.append(step_id)
                workflow.errors.append(_safe_text(exc, 160))
                workflow.state = WorkflowRuntimeState.PARTIAL_SUCCESS if workflow.completed_steps else WorkflowRuntimeState.FAILED
                self.metrics["failed"] += 1
                self.checkpoint(workflow_id, interrupted_step=step_id)
                self._event(workflow_id, "workflow_failed", step.owner_agent, workflow.state.value)
        workflow.updated_at = _now()
        return step

    def pause(self, workflow_id: str) -> WorkflowRecordRuntime:
        workflow = self.require(workflow_id)
        if workflow.state is not WorkflowRuntimeState.RUNNING:
            raise ValueError("workflow_not_running")
        workflow.state = WorkflowRuntimeState.PAUSED
        self.checkpoint(workflow_id, interrupted_step=workflow.current_step)
        self.metrics["paused"] += 1
        self._event(workflow_id, "workflow_paused", "workflow_runtime", "paused")
        return workflow

    def resume(self, workflow_id: str) -> WorkflowRecordRuntime:
        workflow = self.require(workflow_id)
        if workflow.state not in {WorkflowRuntimeState.PAUSED, WorkflowRuntimeState.WAITING}:
            raise ValueError("workflow_not_resumable")
        workflow.state = WorkflowRuntimeState.RUNNING
        self._event(workflow_id, "workflow_resumed", "workflow_runtime", "running")
        return workflow

    def cancel(self, workflow_id: str) -> WorkflowRecordRuntime:
        workflow = self.require(workflow_id)
        if workflow.state in {WorkflowRuntimeState.COMPLETED, WorkflowRuntimeState.CANCELLED}:
            raise ValueError("workflow_not_cancellable")
        workflow.state = WorkflowRuntimeState.CANCELLED
        for step in workflow.steps:
            if step.status in {WorkflowStepState.PENDING, WorkflowStepState.READY, WorkflowStepState.WAITING}:
                step.status = WorkflowStepState.CANCELLED
                workflow.cancelled_steps.append(step.step_id)
        self._event(workflow_id, "workflow_cancelled", "workflow_runtime", "cancelled")
        return workflow

    def checkpoint(self, workflow_id: str, *, interrupted_step: str | None = None) -> RuntimeCheckpoint:
        workflow = self.require(workflow_id)
        if len([item for item in self.checkpoints.values() if item.workflow_id == workflow_id]) >= self.limits.max_checkpoint_history:
            oldest = next(item for item in self.checkpoints.values() if item.workflow_id == workflow_id)
            self.checkpoints.pop(oldest.checkpoint_id, None)
        remaining = tuple(step.step_id for step in workflow.steps if step.step_id not in workflow.completed_steps)
        checkpoint = RuntimeCheckpoint(_id("cp"), workflow_id, workflow.workflow_version, workflow.schema_version, len(workflow.completed_steps), _now(), f"workflow:{workflow_id}", dict(workflow.resource_used), tuple(workflow.completed_steps), remaining, interrupted_step)
        self.checkpoints[checkpoint.checkpoint_id] = checkpoint
        self._event(workflow_id, "checkpoint_created", "checkpoint_runtime", "created")
        return checkpoint

    def restore(self, checkpoint_id: str, *, workflow_version: str | None = None) -> WorkflowRecordRuntime:
        checkpoint = self.checkpoints.get(checkpoint_id)
        if checkpoint is None:
            raise ValueError("checkpoint_not_found_or_corrupt")
        workflow = self.require(checkpoint.workflow_id)
        if checkpoint.schema_version != workflow.schema_version or (workflow_version and checkpoint.workflow_version != workflow_version):
            raise ValueError("checkpoint_version_mismatch")
        if not set(checkpoint.completed_steps) <= {step.step_id for step in workflow.steps}:
            raise ValueError("checkpoint_dependency_integrity_failed")
        workflow.state = WorkflowRuntimeState.RECOVERING
        workflow.completed_steps = list(checkpoint.completed_steps)
        workflow.resource_used = dict(checkpoint.resource_state)
        for step in workflow.steps:
            step.status = WorkflowStepState.COMPLETED if step.step_id in workflow.completed_steps else WorkflowStepState.PENDING
        workflow.current_step = checkpoint.interrupted_step
        self.metrics["recovered"] += 1
        self._event(workflow.workflow_id, "checkpoint_restored", "checkpoint_runtime", "recovering")
        return workflow

    def recover(self, checkpoint_id: str) -> WorkflowRecordRuntime:
        workflow = self.restore(checkpoint_id)
        self.validate(workflow)
        workflow.mode = WorkflowExecutionMode.RECOVERY
        workflow.state = WorkflowRuntimeState.PAUSED
        self._event(workflow.workflow_id, "workflow_recovered", "workflow_runtime", "paused")
        return workflow

    def add_artifact(self, workflow_id: str, artifact_type: str, summary: str, *, owner: str = "prime", persistent: bool = False, provenance: tuple[str, ...] = ()) -> WorkflowArtifact:
        self.require(workflow_id)
        if len(self.artifacts) >= self.limits.max_artifacts:
            raise ValueError("workflow_artifact_limit_reached")
        artifact = WorkflowArtifact(_id("artifact"), workflow_id, _safe_text(owner, 80), _safe_text(artifact_type, 80), "local_private", tuple(_safe_text(item, 160) for item in provenance[:10]), "explicit_approval" if persistent else "temporary", "metadata_only", _safe_text(summary, 500))
        self.artifacts[artifact.artifact_id] = artifact
        return artifact

    def cleanup_plan(self) -> dict[str, Any]:
        temporary = tuple(item.artifact_id for item in self.artifacts.values() if item.retention_policy == "temporary")
        orphaned = tuple(item.checkpoint_id for item in self.checkpoints.values() if item.workflow_id not in self.workflows)
        return {"dry_run": True, "temporary_artifacts": temporary[:50], "orphan_checkpoints": orphaned[:50], "deleted": 0}

    def health(self) -> dict[str, Any]:
        counts = {state.value: sum(item.state is state for item in self.workflows.values()) for state in WorkflowRuntimeState}
        state = "degraded" if counts["failed"] or counts["timed_out"] else "paused" if counts["paused"] else "ready"
        return {"status": state, "counts": counts, "checkpoints": len(self.checkpoints), "artifacts": len(self.artifacts), "authority": "coordination_only"}

    def status(self) -> dict[str, Any]:
        return {"enabled": True, "workflows": len(self.workflows), "active": sum(item.state is WorkflowRuntimeState.RUNNING for item in self.workflows.values()), "paused": sum(item.state is WorkflowRuntimeState.PAUSED for item in self.workflows.values()), "checkpoints": len(self.checkpoints), "default_mode": "interactive", "background_unrestricted": False, "execution_authority": False}

    def require(self, workflow_id: str) -> WorkflowRecordRuntime:
        workflow = self.workflows.get(workflow_id)
        if workflow is None:
            raise ValueError("workflow_not_found")
        return workflow

    def _step(self, workflow: WorkflowRecordRuntime, step_id: str) -> RuntimeWorkflowStep:
        for step in workflow.steps:
            if step.step_id == step_id:
                return step
        raise ValueError("workflow_step_not_found")

    def _event(self, workflow_id: str, event_type: str, component: str, result: str, policy_decision: str = "not_applicable") -> None:
        sequence = sum(item.workflow_id == workflow_id for item in self.events) + 1
        event = WorkflowEvent(_id("event"), workflow_id, event_type, sequence, _now(), component, _safe_text(result, 120), policy_decision)
        self.events = (self.events + [event])[-self.limits.max_event_history:]

    def safe_snapshot(self, workflow_id: str) -> dict[str, Any]:
        workflow = self.require(workflow_id)
        return {"workflow_id": workflow.workflow_id, "type": workflow.workflow_type, "version": workflow.workflow_version, "state": workflow.state.value, "mode": workflow.mode.value, "privacy_scope": workflow.privacy_scope, "approval_state": workflow.approval_state, "steps": len(workflow.steps), "current_step": workflow.current_step, "completed": len(workflow.completed_steps), "failed": len(workflow.failed_steps), "warnings": tuple(workflow.warnings[:10]), "errors": tuple(workflow.errors[:10])}

    def validate_serializable(self) -> bool:
        payload = {"status": self.status(), "events": [asdict(item) for item in self.events]}
        encoded = json.dumps(payload)
        return not SECRET_PATTERN.search(encoded)
