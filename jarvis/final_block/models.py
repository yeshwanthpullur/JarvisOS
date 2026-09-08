"""Typed metadata for Engineering Steps 95-122.

These models describe state and evidence. They do not grant execution authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from jarvis.foundation_common import bounded, new_id, now


class OperationalState(StrEnum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    RECOVERING = "RECOVERING"


class OperatingMode(StrEnum):
    DEVELOPMENT = "DEVELOPMENT"
    TESTING = "TESTING"
    PRODUCTION = "PRODUCTION"
    REVENUE = "REVENUE"
    OFFLINE = "OFFLINE"
    RECOVERY = "RECOVERY"


class StepStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    READY = "READY"
    READY_FOUNDATION = "READY_FOUNDATION"
    IN_PROGRESS = "IN_PROGRESS"
    VERIFIED = "VERIFIED"
    DEGRADED = "DEGRADED"
    UNCONFIGURED = "UNCONFIGURED"
    BLOCKED = "BLOCKED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class CapabilityMatrixRow:
    capability: str
    online: str
    offline: str
    degraded_offline: str
    local_provider: str
    fallback: str
    required_dependency: str

    def __post_init__(self) -> None:
        for value in (self.capability, self.online, self.offline, self.degraded_offline, self.local_provider, self.fallback, self.required_dependency):
            if len(value) > 240:
                raise ValueError("capability_matrix_value_too_long")


@dataclass(frozen=True, slots=True)
class RouteAssessment:
    capability: str
    provider: str
    allowed: bool
    privacy_mode: str
    state: OperationalState
    cost_class: str = "unknown"
    quality_class: str = "unknown"
    reason: str = ""
    evidence_ref: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        object.__setattr__(self, "reason", bounded(self.reason, 400))


@dataclass(frozen=True, slots=True)
class InjectionAssessment:
    allowed_as_data: bool
    detected: bool
    reason: str
    source_type: str = "external"
    assessment_id: str = field(default_factory=new_id)


@dataclass(frozen=True, slots=True)
class WorkspaceDecision:
    allowed: bool
    workspace_ref: str
    reason: str
    decision_id: str = field(default_factory=new_id)


@dataclass(frozen=True, slots=True)
class GoldenCaseResult:
    case_id: str
    category: str
    passed: bool
    status: str
    evidence: str = ""
    warning: str = ""


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    name: str
    total: int
    passed: int
    failed: int
    degraded: int = 0
    warnings: tuple[str, ...] = ()
    report_id: str = field(default_factory=new_id)
    created_at: str = field(default_factory=now)


@dataclass(frozen=True, slots=True)
class RevenueWorkflow:
    workflow_id: str
    name: str
    customer_problem: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    tools: tuple[str, ...]
    quality_gate: tuple[str, ...]
    privacy_class: str = "private"
    status: str = "plan_only"
    human_review_required: bool = True
    cost_class: str = "unknown"
    fallback: str = "manual_review"


@dataclass(frozen=True, slots=True)
class LaptopBaseline:
    status: str
    components: tuple[str, ...]
    local_first: bool = True
    phone_transition_allowed: bool = False
    cloud_required: bool = False
    limitations: tuple[str, ...] = ()
