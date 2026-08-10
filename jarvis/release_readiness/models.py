"""Bounded Prompt 85 release-validation models."""

from dataclasses import dataclass, field
from enum import Enum
from jarvis.foundation_common import bounded, new_id, now


class GateState(str, Enum):
    RUNNING = "running"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
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

    def __post_init__(self) -> None:
        object.__setattr__(self, "gate_id", bounded(self.gate_id, 80))
        object.__setattr__(self, "category", bounded(self.category, 80))
        object.__setattr__(self, "owner", bounded(self.owner, 80))
        object.__setattr__(self, "evidence", tuple(bounded(x, 240) for x in self.evidence[:12]))
        object.__setattr__(self, "warnings", tuple(bounded(x, 240) for x in self.warnings[:12]))


@dataclass(frozen=True, slots=True)
class SystemContract:
    component: str
    authority: str
    ownership: str
    dependencies: tuple[str, ...]
    supported_interactions: tuple[str, ...]
    unsupported_interactions: tuple[str, ...]
    verification_status: GateState


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


@dataclass(frozen=True, slots=True)
class ValidationReport:
    status: GateState
    gates: tuple[ReleaseGate, ...]
    contracts: tuple[SystemContract, ...]
    missing_components: tuple[str, ...]
    warnings: tuple[str, ...]
    report_id: str = field(default_factory=new_id)
    created_at: str = field(default_factory=now)

    @property
    def passed(self) -> int:
        return sum(g.status is GateState.PASSED for g in self.gates)

    @property
    def blocked(self) -> int:
        return sum(g.status is GateState.BLOCKED for g in self.gates)
