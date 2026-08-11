"""Bounded Prompt 85 release-validation models."""

from dataclasses import dataclass, field
from enum import Enum
from jarvis.foundation_common import bounded, new_id, now


class GateState(str, Enum):
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    MANUAL_REVIEW = "manual_review"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class ReleaseGate:
    gate_id: str
    category: str
    status: GateState
    blocking: bool
    owner: str
    evidence: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    timestamp: str = field(default_factory=now)
    gate_name: str = ""
    verification_reference: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_id", bounded(self.gate_id, 80))
        object.__setattr__(self, "category", bounded(self.category, 80))
        object.__setattr__(self, "owner", bounded(self.owner, 80))
        object.__setattr__(self, "evidence", tuple(bounded(x, 240) for x in self.evidence[:12]))
        object.__setattr__(self, "warnings", tuple(bounded(x, 240) for x in self.warnings[:12]))
        object.__setattr__(self, "gate_name", bounded(self.gate_name or self.category, 100))
        object.__setattr__(self, "verification_reference", bounded(self.verification_reference, 240))


@dataclass(frozen=True, slots=True)
class SystemContract:
    component: str
    authority: str
    ownership: str
    dependencies: tuple[str, ...]
    supported_interactions: tuple[str, ...]
    unsupported_interactions: tuple[str, ...]
    verification_status: GateState
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    privacy_scope: str = "request_scoped"
    resource_budget: str = "bounded_by_owner"
    failure_behavior: str = "fail_closed_or_truthful_unavailable"


@dataclass(frozen=True, slots=True)
class ReleaseCandidate:
    version: str
    commit: str
    branch: str
    status: GateState
    gate_ids: tuple[str, ...]
    blocking_gate_ids: tuple[str, ...]
    candidate_id: str = field(default_factory=new_id)
    timestamp: str = field(default_factory=now)
    build_status: GateState = GateState.PASSED
    verification_status: GateState = GateState.WARNING
    documentation_status: GateState = GateState.PASSED
    security_status: GateState = GateState.PASSED
    release_notes_status: GateState = GateState.PASSED

    @property
    def target_commit(self) -> str:
        return self.commit


@dataclass(frozen=True, slots=True)
class CompatibilityEntry:
    source:str; target:str; status:str; supported:tuple[str,...]; unsupported:tuple[str,...]; verification_reference:str


@dataclass(frozen=True, slots=True)
class ValidationScenario:
    scenario_id:str; name:str; expected_path:tuple[str,...]; participants:tuple[str,...]; policies:tuple[str,...]; expected_output:str; expected_failure:str; status:GateState=GateState.PASSED


@dataclass(frozen=True, slots=True)
class ReadinessScore:
    category:str; score:int; status:GateState; evidence:tuple[str,...]
    def __post_init__(self):
        if not 0<=self.score<=100:raise ValueError("invalid_readiness_score")


@dataclass(frozen=True, slots=True)
class ValidationReport:
    status: GateState
    gates: tuple[ReleaseGate, ...]
    contracts: tuple[SystemContract, ...]
    missing_components: tuple[str, ...]
    warnings: tuple[str, ...]
    compatibility: tuple[CompatibilityEntry, ...] = ()
    scenarios: tuple[ValidationScenario, ...] = ()
    scorecard: tuple[ReadinessScore, ...] = ()
    report_id: str = field(default_factory=new_id)
    created_at: str = field(default_factory=now)

    @property
    def passed(self) -> int:
        return sum(g.status is GateState.PASSED for g in self.gates)

    @property
    def blocked(self) -> int:
        return sum(g.status is GateState.BLOCKED for g in self.gates)

    @property
    def mandatory_passed(self)->bool:
        return all(not gate.blocking or gate.status is GateState.PASSED for gate in self.gates)
