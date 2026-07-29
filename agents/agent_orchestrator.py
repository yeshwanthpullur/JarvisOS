"""Governed multi-agent coordination built on the existing Agent Framework."""

from __future__ import annotations

import json
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from agents.agent_capabilities import AgentCapability
from agents.agent_goal import AgentGoal
from agents.agent_permissions import AgentPermission
from agents.agent_profile import TrustLevel
from agents.agent_registry import AgentRegistry
from agents.agent_result import AgentResult, AgentResultStatus
from agents.agent_state import AgentState
from agents.agent_status import AgentStatus
from agents.agent_task import AgentTask


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CollaborationMode(StrEnum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    REVIEW = "review"
    DEBATE = "debate"
    SPECIALIST_PANEL = "specialist_panel"
    PLANNER_EXECUTOR = "planner_executor"
    RESEARCH_VERIFICATION = "research_verification"


class MultiAgentMode(StrEnum):
    OFF = "off"
    CONFIRM = "confirm"
    AUTOMATIC_SAFE = "automatic-safe"
    AUTOMATIC = "automatic"


class CoordinationStatus(StrEnum):
    PENDING_APPROVAL = "pending_approval"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class MultiAgentLimits:
    maximum_agents: int = 4
    maximum_subtasks: int = 8
    maximum_recursion_depth: int = 1
    maximum_retries: int = 1
    maximum_parallel_executions: int = 2
    maximum_total_timeout_seconds: int = 180


@dataclass(frozen=True, slots=True)
class MultiAgentAssessment:
    requires_multi_agent: bool
    reason: str
    suggested_agents: tuple[str, ...] = ()
    collaboration_mode: CollaborationMode = CollaborationMode.REVIEW
    estimated_cost_class: str = "low"
    estimated_latency_class: str = "moderate"
    approval_requirement: str = "executive"
    confidence: float = 0.0


@dataclass(frozen=True, slots=True)
class DelegatedSubtask:
    subtask_id: str
    assigned_agent_id: str
    objective: str
    allowed_context: dict[str, Any] = field(default_factory=dict)
    allowed_providers: tuple[str, ...] = ()
    allowed_tools: tuple[str, ...] = ()
    permission_scope: tuple[str, ...] = ("providers",)
    expected_evidence: tuple[str, ...] = ()
    expected_output: str = "text"
    timeout_seconds: int = 60
    dependency_ids: tuple[str, ...] = ()
    status: AgentResultStatus = AgentResultStatus.READY


@dataclass(frozen=True, slots=True)
class DelegationPlan:
    coordination_id: str
    parent_request_id: str
    objective: str
    collaboration_mode: CollaborationMode
    participating_agents: tuple[str, ...]
    subtasks: tuple[DelegatedSubtask, ...]
    dependencies: dict[str, tuple[str, ...]] = field(default_factory=dict)
    execution_order: tuple[str, ...] = ()
    parallel_groups: tuple[tuple[str, ...], ...] = ()
    required_context: dict[str, Any] = field(default_factory=dict)
    expected_output_schema: str = "text"
    permissions_required: tuple[str, ...] = ("providers",)
    approval_requirements: tuple[str, ...] = ("executive",)
    provider_policy: str = "automatic"
    tool_policy: str = "none"
    timeout_seconds: int = 180
    retry_limits: int = 1
    completion_criteria: str = "At least one valid result and a bounded synthesis."
    synthesis_strategy: str = "evidence_aware"
    cancellation_policy: str = "cooperative"
    validated: bool = False


@dataclass(frozen=True, slots=True)
class AgentConflict:
    claim: str
    agent_ids: tuple[str, ...]
    reason: str
    resolved: bool = False


@dataclass(frozen=True, slots=True)
class CoordinationRecord:
    coordination_id: str
    parent_request_id: str
    objective: str
    mode: CollaborationMode
    status: CoordinationStatus
    plan: DelegationPlan
    results: tuple[AgentResult, ...] = ()
    conflicts: tuple[AgentConflict, ...] = ()
    synthesis: str = ""
    warnings: tuple[str, ...] = ()
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True, slots=True)
class AgentOrchestrationPlan:
    """Backward-compatible basic plan used by the original Agent Framework API."""

    goal: AgentGoal
    tasks: tuple[AgentTask, ...] = ()
    dependencies: dict[str, tuple[str, ...]] = field(default_factory=dict)


class CoordinationStore:
    """Bounded JSON persistence for observable coordination records."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory
        self._records: dict[str, CoordinationRecord] = {}
        if directory is not None:
            directory.mkdir(parents=True, exist_ok=True)
            self._load()

    def save(self, record: CoordinationRecord) -> None:
        self._records[record.coordination_id] = record
        if self.directory is None:
            return
        path = self.directory / f"{record.coordination_id}.json"
        path.write_text(json.dumps(self._serialize(record), indent=2, sort_keys=True), encoding="utf-8")

    def get(self, coordination_id: str) -> CoordinationRecord | None:
        return self._records.get(coordination_id)

    def list(self) -> tuple[CoordinationRecord, ...]:
        return tuple(sorted(self._records.values(), key=lambda item: item.created_at, reverse=True))

    def _load(self) -> None:
        assert self.directory is not None
        for path in self.directory.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                record = self._deserialize(data)
                if record.status is CoordinationStatus.RUNNING:
                    record = replace(
                        record,
                        status=CoordinationStatus.PARTIALLY_COMPLETED,
                        warnings=(*record.warnings, "Interrupted coordination was not resumed automatically."),
                    )
                self._records[record.coordination_id] = record
            except (OSError, ValueError, TypeError, KeyError):
                continue

    def _serialize(self, record: CoordinationRecord) -> dict[str, Any]:
        def normalize(value: Any) -> Any:
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, StrEnum):
                return value.value
            if isinstance(value, tuple):
                return [normalize(item) for item in value]
            if isinstance(value, dict):
                return {str(key): normalize(item) for key, item in value.items()}
            return value

        return normalize(asdict(record))

    def _deserialize(self, data: dict[str, Any]) -> CoordinationRecord:
        subtasks = tuple(
            DelegatedSubtask(
                **{
                    **item,
                    "dependency_ids": tuple(item.get("dependency_ids", ())),
                    "allowed_providers": tuple(item.get("allowed_providers", ())),
                    "allowed_tools": tuple(item.get("allowed_tools", ())),
                    "permission_scope": tuple(item.get("permission_scope", ())),
                    "expected_evidence": tuple(item.get("expected_evidence", ())),
                    "status": AgentResultStatus(item.get("status", "ready")),
                }
            )
            for item in data["plan"]["subtasks"]
        )
        plan_data = dict(data["plan"])
        plan_data.update(
            collaboration_mode=CollaborationMode(plan_data["collaboration_mode"]),
            participating_agents=tuple(plan_data["participating_agents"]),
            subtasks=subtasks,
            execution_order=tuple(plan_data.get("execution_order", ())),
            parallel_groups=tuple(tuple(group) for group in plan_data.get("parallel_groups", ())),
            permissions_required=tuple(plan_data.get("permissions_required", ())),
            approval_requirements=tuple(plan_data.get("approval_requirements", ())),
            dependencies={key: tuple(value) for key, value in plan_data.get("dependencies", {}).items()},
        )
        results = tuple(
            AgentResult(
                **{
                    **item,
                    "status": AgentResultStatus(item.get("status", "completed")),
                    "evidence": tuple(item.get("evidence", ())),
                    "sources": tuple(item.get("sources", ())),
                    "assumptions": tuple(item.get("assumptions", ())),
                    "warnings": tuple(item.get("warnings", ())),
                    "errors": tuple(item.get("errors", ())),
                    "started_at": datetime.fromisoformat(item["started_at"]) if item.get("started_at") else None,
                    "completed_at": datetime.fromisoformat(item["completed_at"]) if item.get("completed_at") else None,
                }
            )
            for item in data.get("results", ())
        )
        conflicts = tuple(
            AgentConflict(
                claim=item["claim"],
                agent_ids=tuple(item.get("agent_ids", ())),
                reason=item["reason"],
                resolved=bool(item.get("resolved", False)),
            )
            for item in data.get("conflicts", ())
        )
        return CoordinationRecord(
            coordination_id=data["coordination_id"],
            parent_request_id=data["parent_request_id"],
            objective=data["objective"],
            mode=CollaborationMode(data["mode"]),
            status=CoordinationStatus(data["status"]),
            plan=DelegationPlan(**plan_data),
            results=results,
            conflicts=conflicts,
            synthesis=data.get("synthesis", ""),
            warnings=tuple(data.get("warnings", ())),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


class AgentOrchestrator:
    """Coordinates bounded, provider-backed collaboration under Executive authority."""

    def __init__(
        self,
        registry: AgentRegistry | None = None,
        execution_manager: Any | None = None,
        workspace_dir: Path | None = None,
        limits: MultiAgentLimits | None = None,
        max_parallel: int | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.registry = registry or AgentRegistry()
        self.execution_manager = execution_manager
        base_limits = limits or MultiAgentLimits()
        self.limits = replace(
            base_limits,
            maximum_parallel_executions=max(1, min(max_parallel or base_limits.maximum_parallel_executions, 4)),
        )
        self.mode = MultiAgentMode.AUTOMATIC_SAFE
        self.store = CoordinationStore(workspace_dir / "coordinations" if workspace_dir else None)
        self._logger = logger or logging.getLogger(__name__)
        self._cancellations: dict[str, threading.Event] = {}
        self.initialized = True

    def receive_objective(self, goal: AgentGoal) -> AgentOrchestrationPlan:
        return AgentOrchestrationPlan(goal=goal)

    def assign_tasks(self, plan: AgentOrchestrationPlan) -> tuple[AgentTask, ...]:
        return plan.tasks

    def collect_results(self, results: tuple[AgentResult, ...]) -> tuple[AgentResult, ...]:
        return results

    def assess(self, objective: str, metadata: dict[str, Any] | None = None) -> MultiAgentAssessment:
        metadata = metadata or {}
        lowered = objective.lower()
        explicit = any(marker in lowered for marker in ("multi-agent", "multiagent", "planner and reviewer", "independent review", "specialist panel"))
        verification = any(marker in lowered for marker in ("review and verify", "research and verify", "independently verify", "debate"))
        domains = sum(marker in lowered for marker in ("research", "plan", "security", "code", "architecture", "review", "cost", "risk"))
        complex_enough = len(objective.split()) >= 35 and domains >= 2
        required = self.mode is not MultiAgentMode.OFF and (explicit or verification or complex_enough)
        mode = self._mode_for(lowered)
        if self.mode is MultiAgentMode.CONFIRM and not metadata.get("multiagent_approved"):
            required = False
            reason = "Multi-agent work requires explicit approval in confirm mode."
        elif required:
            reason = "The request benefits from bounded specialization and independent review."
        else:
            reason = "A single provider-backed response is sufficient."
        assessment = MultiAgentAssessment(
            requires_multi_agent=required,
            reason=reason,
            suggested_agents=("planner", "reviewer") if required else (),
            collaboration_mode=mode,
            estimated_cost_class="moderate" if required else "low",
            estimated_latency_class="moderate" if required else "low",
            approval_requirement="executive_and_user" if self.mode is MultiAgentMode.CONFIRM else "executive",
            confidence=0.9 if explicit else (0.75 if verification or complex_enough else 0.9),
        )
        self._logger.info(
            "multiagent_assessment_completed request_id=%s requires_multi_agent=%s collaboration_mode=%s confidence=%s",
            metadata.get("request_id", "unknown"),
            assessment.requires_multi_agent,
            assessment.collaboration_mode.value,
            assessment.confidence,
        )
        return assessment

    def select_agents(self, capabilities: Iterable[AgentCapability]) -> tuple[Any, ...]:
        required = tuple(capabilities)
        selected: list[Any] = []
        allowed_trust = {TrustLevel.SYSTEM, TrustLevel.CORE, TrustLevel.TRUSTED, TrustLevel.VERIFIED}
        for agent in self.registry.list_agents():
            record = self.registry.require(agent.agent_id)
            reasons: list[str] = []
            if not record.enabled or agent.state in {AgentState.DISABLED, AgentState.FAILED, AgentState.SHUTDOWN, AgentState.DESTROYED}:
                reasons.append("disabled_or_unavailable")
            if agent.health().status not in {AgentStatus.HEALTHY, AgentStatus.RUNNING, AgentStatus.IDLE}:
                reasons.append("unhealthy")
            if agent.profile.trust_level not in allowed_trust:
                reasons.append("trust_boundary")
            if AgentPermission.PROVIDERS not in agent.profile.permissions:
                reasons.append("provider_permission_missing")
            provider_names = set(getattr(agent.context.provider_router, "provider_names", ()))
            if agent.profile.required_providers and not set(agent.profile.required_providers).issubset(provider_names):
                reasons.append("required_provider_missing")
            if agent.profile.configuration.get("required_tools"):
                reasons.append("required_tools_not_authorized")
            if required and not any(capability in agent.profile.capabilities for capability in required):
                reasons.append("capability_mismatch")
            if reasons:
                self._logger.info("agent_rejected agent_id=%s reason=%s", agent.agent_id, ",".join(reasons))
                continue
            selected.append(agent)
            self._logger.info("agent_selected agent_id=%s reason=capability_health_permission_match", agent.agent_id)
        selected.sort(key=lambda item: item.profile.priority)
        return tuple(selected[: self.limits.maximum_agents])

    def create_delegation_plan(
        self,
        objective: str,
        parent_request_id: str,
        assessment: MultiAgentAssessment,
        metadata: dict[str, Any] | None = None,
    ) -> DelegationPlan:
        metadata = metadata or {}
        agents = self.select_agents((AgentCapability.PLANNING, AgentCapability.REASONING, AgentCapability.REFLECTION))
        planner = next((agent for agent in agents if AgentCapability.PLANNING in agent.profile.capabilities), None)
        reviewer = next((agent for agent in agents if AgentCapability.REFLECTION in agent.profile.capabilities), None)
        if planner is None or reviewer is None:
            raise LookupError("No compatible planner and reviewer agents are available.")
        coordination_id = str(uuid4())
        first_id, second_id = str(uuid4()), str(uuid4())
        second_dependencies = (first_id,) if assessment.collaboration_mode in {CollaborationMode.SEQUENTIAL, CollaborationMode.REVIEW, CollaborationMode.PLANNER_EXECUTOR} else ()
        safe_context = self._minimize_context(metadata.get("selected_context", {}))
        provider = metadata.get("provider_preference")
        subtasks = (
            DelegatedSubtask(
                subtask_id=first_id,
                assigned_agent_id=planner.agent_id,
                objective=f"Produce a concise evidence-aware plan for: {objective}",
                allowed_context=safe_context,
                allowed_providers=(str(provider),) if provider else (),
                expected_evidence=("state assumptions", "identify uncertainty"),
            ),
            DelegatedSubtask(
                subtask_id=second_id,
                assigned_agent_id=reviewer.agent_id,
                objective=f"Review the proposed answer for correctness, omissions, and unsupported claims: {objective}",
                allowed_context=safe_context,
                allowed_providers=(str(provider),) if provider else (),
                expected_evidence=("identify supported claims", "identify unresolved issues"),
                dependency_ids=second_dependencies,
            ),
        )
        plan = DelegationPlan(
            coordination_id=coordination_id,
            parent_request_id=parent_request_id,
            objective=objective,
            collaboration_mode=assessment.collaboration_mode,
            participating_agents=(planner.agent_id, reviewer.agent_id),
            subtasks=subtasks,
            dependencies={second_id: second_dependencies},
            execution_order=(first_id, second_id),
            parallel_groups=((first_id, second_id),) if not second_dependencies else (),
            required_context=safe_context,
            provider_policy=str(metadata.get("execution_policy", "automatic")),
            timeout_seconds=min(int(metadata.get("timeout_seconds", self.limits.maximum_total_timeout_seconds) or self.limits.maximum_total_timeout_seconds), self.limits.maximum_total_timeout_seconds),
            retry_limits=self.limits.maximum_retries,
        )
        self._logger.info(
            "delegation_plan_created request_id=%s coordination_id=%s collaboration_mode=%s agents=%s",
            parent_request_id,
            coordination_id,
            assessment.collaboration_mode.value,
            len(plan.participating_agents),
        )
        return self.validate_plan(plan)

    def validate_plan(self, plan: DelegationPlan) -> DelegationPlan:
        errors: list[str] = []
        if len(plan.participating_agents) > self.limits.maximum_agents:
            errors.append("maximum_agents_exceeded")
        if len(plan.subtasks) > self.limits.maximum_subtasks:
            errors.append("maximum_subtasks_exceeded")
        if plan.tool_policy != "none" or any(subtask.allowed_tools for subtask in plan.subtasks):
            errors.append("tools_not_authorized")
        subtask_ids = {subtask.subtask_id for subtask in plan.subtasks}
        if len(subtask_ids) != len(plan.subtasks):
            errors.append("duplicate_subtask_id")
        if any(dependency not in subtask_ids for subtask in plan.subtasks for dependency in subtask.dependency_ids):
            errors.append("invalid_dependency")
        if errors:
            raise ValueError("Invalid delegation plan: " + ", ".join(errors))
        validated = replace(plan, validated=True)
        self._logger.info(
            "delegation_plan_validated request_id=%s coordination_id=%s collaboration_mode=%s",
            plan.parent_request_id,
            plan.coordination_id,
            plan.collaboration_mode.value,
        )
        return validated

    def coordinate(
        self,
        objective: str,
        parent_request_id: str,
        assessment: MultiAgentAssessment,
        metadata: dict[str, Any] | None = None,
        executive_approved: bool = False,
    ) -> CoordinationRecord:
        metadata = metadata or {}
        plan = self.create_delegation_plan(objective, parent_request_id, assessment, metadata)
        status = CoordinationStatus.READY if executive_approved else CoordinationStatus.PENDING_APPROVAL
        record = CoordinationRecord(plan.coordination_id, parent_request_id, objective, plan.collaboration_mode, status, plan)
        self.store.save(record)
        self._logger.info("coordination_created request_id=%s coordination_id=%s status=%s", parent_request_id, plan.coordination_id, status.value)
        if not executive_approved:
            return record
        return self.dispatch(record, metadata)

    def dispatch(self, record: CoordinationRecord, metadata: dict[str, Any] | None = None) -> CoordinationRecord:
        if self.execution_manager is None:
            return self._finish_failure(record, "Provider Execution Manager is unavailable.")
        metadata = metadata or {}
        cancellation = threading.Event()
        self._cancellations[record.coordination_id] = cancellation
        running = replace(record, status=CoordinationStatus.RUNNING, updated_at=utc_now())
        self.store.save(running)
        results: list[AgentResult] = []
        by_id: dict[str, AgentResult] = {}
        try:
            if record.plan.parallel_groups:
                with ThreadPoolExecutor(max_workers=self.limits.maximum_parallel_executions) as pool:
                    futures = {
                        pool.submit(self._dispatch_subtask, record, subtask, metadata, (), cancellation): subtask
                        for subtask in record.plan.subtasks
                    }
                    for future in as_completed(futures):
                        result = future.result()
                        results.append(result)
                        by_id[result.subtask_id or ""] = result
            else:
                for subtask in record.plan.subtasks:
                    if cancellation.is_set():
                        results.append(self._cancelled_result(record, subtask))
                        continue
                    dependency_results = tuple(by_id[item] for item in subtask.dependency_ids if item in by_id)
                    if any(item.status is not AgentResultStatus.COMPLETED for item in dependency_results):
                        result = self._blocked_result(record, subtask, "Required dependency did not complete.")
                    else:
                        result = self._dispatch_subtask(record, subtask, metadata, dependency_results, cancellation)
                    results.append(result)
                    by_id[subtask.subtask_id] = result
            conflicts = self.analyze_conflicts(tuple(results), record.mode)
            completed = tuple(item for item in results if item.status is AgentResultStatus.COMPLETED)
            if not completed:
                return self._finish_failure(running, "No agent completed successfully.", tuple(results))
            synthesis = self.synthesize(running, completed, conflicts, metadata, cancellation)
            failed = tuple(item for item in results if item.status is not AgentResultStatus.COMPLETED)
            final_status = CoordinationStatus.PARTIALLY_COMPLETED if failed else CoordinationStatus.COMPLETED
            finished = replace(
                running,
                status=final_status,
                results=tuple(results),
                conflicts=conflicts,
                synthesis=synthesis,
                warnings=tuple(f"{item.agent_id}: {item.status.value}" for item in failed),
                updated_at=utc_now(),
            )
            self.store.save(finished)
            event = "coordination_partially_completed" if failed else "coordination_completed"
            self._logger.info("%s request_id=%s coordination_id=%s status=%s", event, record.parent_request_id, record.coordination_id, final_status.value)
            return finished
        finally:
            self._cancellations.pop(record.coordination_id, None)

    def synthesize(
        self,
        record: CoordinationRecord,
        results: tuple[AgentResult, ...],
        conflicts: tuple[AgentConflict, ...],
        metadata: dict[str, Any],
        cancellation: threading.Event,
    ) -> str:
        if cancellation.is_set():
            return "Coordination was cancelled before synthesis."
        authorized = "\n\n".join(f"[{item.agent_id}] {item.content}" for item in results)
        conflict_text = "\n".join(item.reason for item in conflicts) or "No material conflict detected."
        prompt = (
            "Synthesize the authorized agent outputs below into a concise final answer. "
            "Preserve supported conclusions, label assumptions, disclose unresolved conflicts and partial failures, "
            "and do not request or execute tools.\n\n"
            f"Objective: {record.objective}\n\nAgent outputs:\n{authorized}\n\nConflict analysis:\n{conflict_text}"
        )
        self._logger.info("synthesis_started request_id=%s coordination_id=%s", record.parent_request_id, record.coordination_id)
        result = self._provider_call(record, "coordinator", str(uuid4()), prompt, metadata)
        if result.status is not AgentResultStatus.COMPLETED:
            fallback = "\n\n".join(item.content for item in results)
            return f"Partial synthesis (synthesis provider failed):\n{fallback}"
        self._logger.info("synthesis_completed request_id=%s coordination_id=%s provider_id=%s", record.parent_request_id, record.coordination_id, result.provider_metadata.get("provider_id"))
        return result.content

    def analyze_conflicts(self, results: tuple[AgentResult, ...], mode: CollaborationMode) -> tuple[AgentConflict, ...]:
        completed = [item for item in results if item.status is AgentResultStatus.COMPLETED and item.content.strip()]
        if len(completed) < 2 or mode not in {CollaborationMode.DEBATE, CollaborationMode.RESEARCH_VERIFICATION, CollaborationMode.SPECIALIST_PANEL}:
            return ()
        normalized = {" ".join(item.content.lower().split()) for item in completed}
        if len(normalized) == 1:
            return ()
        conflict = AgentConflict(
            claim="Agent conclusions differ and require evidence-aware synthesis.",
            agent_ids=tuple(item.agent_id for item in completed),
            reason="Distinct conclusions were preserved; agreement was not inferred by majority vote.",
        )
        self._logger.info("agent_conflict_detected coordination_id=%s agent_ids=%s", completed[0].coordination_id, ",".join(conflict.agent_ids))
        return (conflict,)

    def cancel(self, coordination_id: str) -> bool:
        record = self.store.get(coordination_id)
        if record is None or record.status in {CoordinationStatus.COMPLETED, CoordinationStatus.FAILED, CoordinationStatus.CANCELLED}:
            return False
        event = self._cancellations.get(coordination_id)
        if event is not None:
            event.set()
        cancelled = replace(record, status=CoordinationStatus.CANCELLED, updated_at=utc_now())
        self.store.save(cancelled)
        self._logger.info("agent_dispatch_cancelled request_id=%s coordination_id=%s status=cancelled", record.parent_request_id, coordination_id)
        return True

    def set_mode(self, mode: str | MultiAgentMode) -> MultiAgentMode:
        self.mode = mode if isinstance(mode, MultiAgentMode) else MultiAgentMode(mode)
        return self.mode

    def status(self) -> dict[str, Any]:
        records = self.store.list()
        return {
            "mode": self.mode.value,
            "coordinations": len(records),
            "active": sum(item.status in {CoordinationStatus.READY, CoordinationStatus.RUNNING, CoordinationStatus.PENDING_APPROVAL} for item in records),
            "limits": asdict(self.limits),
        }

    def _dispatch_subtask(
        self,
        record: CoordinationRecord,
        subtask: DelegatedSubtask,
        metadata: dict[str, Any],
        dependency_results: tuple[AgentResult, ...],
        cancellation: threading.Event,
    ) -> AgentResult:
        if cancellation.is_set():
            return self._cancelled_result(record, subtask)
        dependency_context = "\n\n".join(item.content for item in dependency_results)
        prompt = subtask.objective
        if dependency_context:
            prompt += f"\n\nAuthorized prior output to review:\n{dependency_context}"
        self._logger.info(
            "agent_dispatch_started request_id=%s coordination_id=%s subtask_id=%s agent_id=%s collaboration_mode=%s",
            record.parent_request_id,
            record.coordination_id,
            subtask.subtask_id,
            subtask.assigned_agent_id,
            record.mode.value,
        )
        return self._provider_call(record, subtask.assigned_agent_id, subtask.subtask_id, prompt, metadata)

    def _provider_call(self, record: CoordinationRecord, agent_id: str, subtask_id: str, prompt: str, metadata: dict[str, Any]) -> AgentResult:
        started = utc_now()
        response = None
        last_error: Exception | None = None
        retry_count = 0
        for attempt in range(record.plan.retry_limits + 1):
            retry_count = attempt
            request = self.execution_manager.build_execution_request(
                intent=prompt,
                goal=prompt,
                request_id=subtask_id,
                conversation_id=metadata.get("conversation_id"),
                provider=metadata.get("provider_preference"),
                model=metadata.get("model_preference"),
                context=self._minimize_context(metadata.get("selected_context", {})),
                metadata={
                    "parent_request_id": record.parent_request_id,
                    "coordination_id": record.coordination_id,
                    "subtask_id": subtask_id,
                    "agent_id": agent_id,
                    "execution_policy": metadata.get("execution_policy", record.plan.provider_policy),
                    "local_only": bool(metadata.get("local_only")),
                    "cloud_only": bool(metadata.get("cloud_only")),
                    "task_type": "chat",
                    "timeout_seconds": min(record.plan.timeout_seconds, 60),
                    "tool_policy": "none",
                    "multiagent_depth": 1,
                    "attempt": attempt + 1,
                },
            )
            try:
                response = self.execution_manager.execute_through_provider_router(request)
                if response.success:
                    break
            except Exception as exc:
                last_error = exc
            if attempt < record.plan.retry_limits:
                self._logger.info(
                    "agent_dispatch_retry request_id=%s coordination_id=%s subtask_id=%s agent_id=%s retry_count=%s",
                    record.parent_request_id,
                    record.coordination_id,
                    subtask_id,
                    agent_id,
                    attempt + 1,
                )
        if response is None:
            message = str(last_error or "Provider execution failed.")
            self._logger.info(
                "agent_dispatch_failed request_id=%s coordination_id=%s subtask_id=%s agent_id=%s failure_reason=%s",
                record.parent_request_id,
                record.coordination_id,
                subtask_id,
                agent_id,
                type(last_error).__name__ if last_error else "provider_failure",
            )
            return AgentResult(
                agent_id=agent_id,
                success=False,
                error=message,
                coordination_id=record.coordination_id,
                parent_request_id=record.parent_request_id,
                subtask_id=subtask_id,
                status=AgentResultStatus.FAILED,
                errors=(message,),
                started_at=started,
                completed_at=utc_now(),
                retry_count=retry_count,
            )
        failure_text = " ".join(
            (
                response.response,
                *response.warnings,
                *(str(value) for value in response.diagnostics.values()),
            )
        ).lower()
        if response.success and response.response.strip():
            status = AgentResultStatus.COMPLETED
        elif "timeout" in failure_text or "timed out" in failure_text:
            status = AgentResultStatus.TIMED_OUT
        else:
            status = AgentResultStatus.FAILED
        result = AgentResult(
            agent_id=agent_id,
            success=status is AgentResultStatus.COMPLETED,
            output=response.response,
            error=None if response.success else response.response,
            coordination_id=record.coordination_id,
            parent_request_id=record.parent_request_id,
            subtask_id=subtask_id,
            status=status,
            content=response.response,
            confidence=0.7 if response.success else 0.0,
            warnings=response.warnings,
            errors=() if response.success else (response.response,),
            provider_metadata={
                "provider_id": response.provider,
                "model_id": response.model,
                "latency_ms": response.latency_ms,
                "usage": dict(response.token_metadata),
                "diagnostics": dict(response.diagnostics),
            },
            tool_metadata={"authorized_tools": (), "tools_executed": ()},
            started_at=started,
            completed_at=utc_now(),
            latency_ms=response.latency_ms,
            retry_count=retry_count,
        )
        event = {
            AgentResultStatus.COMPLETED: "agent_dispatch_completed",
            AgentResultStatus.TIMED_OUT: "agent_dispatch_timed_out",
        }.get(status, "agent_dispatch_failed")
        self._logger.info(
            "%s request_id=%s coordination_id=%s subtask_id=%s agent_id=%s provider_id=%s status=%s retry_count=%s",
            event,
            record.parent_request_id,
            record.coordination_id,
            subtask_id,
            agent_id,
            response.provider,
            status.value,
            retry_count,
        )
        self._logger.info(
            "agent_result_normalized request_id=%s coordination_id=%s subtask_id=%s agent_id=%s status=%s",
            record.parent_request_id,
            record.coordination_id,
            subtask_id,
            agent_id,
            status.value,
        )
        return result

    def _finish_failure(self, record: CoordinationRecord, reason: str, results: tuple[AgentResult, ...] = ()) -> CoordinationRecord:
        failed = replace(record, status=CoordinationStatus.FAILED, results=results, warnings=(*record.warnings, reason), updated_at=utc_now())
        self.store.save(failed)
        self._logger.info("coordination_failed request_id=%s coordination_id=%s failure_reason=%s", record.parent_request_id, record.coordination_id, reason)
        return failed

    def _cancelled_result(self, record: CoordinationRecord, subtask: DelegatedSubtask) -> AgentResult:
        return AgentResult(
            agent_id=subtask.assigned_agent_id,
            success=False,
            coordination_id=record.coordination_id,
            parent_request_id=record.parent_request_id,
            subtask_id=subtask.subtask_id,
            status=AgentResultStatus.CANCELLED,
            errors=("Coordination cancelled.",),
        )

    def _blocked_result(self, record: CoordinationRecord, subtask: DelegatedSubtask, reason: str) -> AgentResult:
        return AgentResult(
            agent_id=subtask.assigned_agent_id,
            success=False,
            coordination_id=record.coordination_id,
            parent_request_id=record.parent_request_id,
            subtask_id=subtask.subtask_id,
            status=AgentResultStatus.BLOCKED,
            errors=(reason,),
        )

    def _minimize_context(self, context: Any) -> dict[str, Any]:
        if not isinstance(context, dict):
            return {}
        allowed = {"active_objective", "next_step", "resolved_item", "pending_state", "status", "confidence"}
        return {key: value for key, value in context.items() if key in allowed and value not in (None, "", (), {}, [])}

    def _mode_for(self, objective: str) -> CollaborationMode:
        if "debate" in objective:
            return CollaborationMode.DEBATE
        if "research" in objective and ("verify" in objective or "review" in objective):
            return CollaborationMode.RESEARCH_VERIFICATION
        if "parallel" in objective:
            return CollaborationMode.PARALLEL
        if "specialist panel" in objective:
            return CollaborationMode.SPECIALIST_PANEL
        if "planner and executor" in objective:
            return CollaborationMode.PLANNER_EXECUTOR
        if "review" in objective or "verify" in objective or "planner and reviewer" in objective:
            return CollaborationMode.REVIEW
        return CollaborationMode.SEQUENTIAL
