"""Typed, bounded models for the Phase 3 agent protocol."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


MAX_NAME = 80
MAX_DESCRIPTION = 600
MAX_INPUT = 4000
MAX_OUTPUT = 8000
MAX_ITEMS = 32


def _bounded(value: object, limit: int) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _bounded_tuple(values: tuple[str, ...], limit: int = MAX_ITEMS) -> tuple[str, ...]:
    return tuple(_bounded(value, MAX_DESCRIPTION) for value in values[:limit])


class AgentStatus(str, Enum):
    READY = "ready"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"
    NOT_CONFIGURED = "not_configured"
    ERROR = "error"


class AgentRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentExecutionMode(str, Enum):
    PLAN_ONLY = "plan_only"
    DRY_RUN = "dry_run"
    APPROVED_EXECUTION = "approved_execution"
    BLOCKED = "blocked"


class AgentApprovalState(str, Enum):
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    GRANTED = "granted"
    DENIED = "denied"
    EXPIRED = "expired"


class AgentResultStatus(str, Enum):
    COMPLETED = "completed"
    PLANNED = "planned"
    BLOCKED = "blocked"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    NEEDS_APPROVAL = "needs_approval"


class AgentCapabilityType(str, Enum):
    CONVERSATION = "conversation"
    MEMORY = "memory"
    VISION = "vision"
    IMAGE = "image"
    VIDEO = "video"
    WEB = "web"
    SYNC = "sync"
    RESEARCH = "research"
    CODING = "coding"
    DOCUMENTS = "documents"
    SCHEDULER = "scheduler"
    ADAPTER = "adapter"
    EVALUATION = "evaluation"
    TOOLS = "tools"
    WORKFLOW = "workflow"
    SYSTEM = "system"
    COMMUNICATION = "communication"
    ROBOTICS = "robotics"
    DRONE = "drone"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class AgentCapability:
    name: str
    capability_type: AgentCapabilityType
    description: str
    input_types: tuple[str, ...] = ()
    output_types: tuple[str, ...] = ()
    side_effects: tuple[str, ...] = ()
    required_permissions: tuple[str, ...] = ()
    risk_level: AgentRiskLevel = AgentRiskLevel.LOW
    local_only: bool = True
    requires_approval: bool = False
    enabled: bool = True
    provider_requirements: tuple[str, ...] = ()
    configuration_requirements: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip() or len(self.name) > MAX_NAME:
            raise ValueError("invalid_agent_capability_name")
        if len(self.description) > MAX_DESCRIPTION:
            raise ValueError("agent_capability_description_too_long")
        if self.side_effects and not self.requires_approval:
            raise ValueError("side_effects_require_approval")
        for values in (
            self.input_types,
            self.output_types,
            self.side_effects,
            self.required_permissions,
            self.provider_requirements,
            self.configuration_requirements,
            self.limitations,
        ):
            if len(values) > MAX_ITEMS:
                raise ValueError("agent_capability_items_exceeded")


@dataclass(frozen=True, slots=True)
class AgentRegistryEntry:
    name: str
    display_name: str
    description: str
    version: str = "1.0"
    status: AgentStatus = AgentStatus.UNAVAILABLE
    capabilities: tuple[AgentCapability, ...] = ()
    local_only: bool = True
    enabled: bool = False
    health: str = "unavailable"
    reason: str = "Not configured."
    owner_subsystem: str = "agents"
    registered_at: str = "phase3"

    def __post_init__(self) -> None:
        if not self.name.strip() or len(self.name) > MAX_NAME:
            raise ValueError("invalid_agent_name")
        if len(self.display_name) > MAX_NAME or len(self.description) > MAX_DESCRIPTION:
            raise ValueError("agent_entry_text_too_long")
        names = [item.name for item in self.capabilities]
        if len(names) != len(set(names)):
            raise ValueError("duplicate_agent_capability")
        if self.status is AgentStatus.READY and not self.enabled:
            raise ValueError("ready_agent_must_be_enabled")


@dataclass(frozen=True, slots=True)
class AgentRequest:
    user_input: str
    normalized_intent: str
    required_capability: AgentCapabilityType = AgentCapabilityType.UNKNOWN
    request_id: str = field(default_factory=lambda: str(uuid4()))
    context_refs: tuple[str, ...] = ()
    memory_refs: tuple[str, ...] = ()
    preferred_agent: str | None = None
    preferred_model: str | None = None
    approval_state: AgentApprovalState = AgentApprovalState.NOT_REQUIRED
    risk_level: AgentRiskLevel = AgentRiskLevel.LOW
    execution_mode: AgentExecutionMode = AgentExecutionMode.PLAN_ONLY
    local_only: bool = True
    created_at: str = "phase3"

    def __post_init__(self) -> None:
        if not self.request_id or len(self.request_id) > MAX_NAME:
            raise ValueError("invalid_agent_request_id")
        if not self.user_input.strip() or len(self.user_input) > MAX_INPUT:
            raise ValueError("invalid_agent_user_input")
        if len(self.normalized_intent) > MAX_DESCRIPTION:
            raise ValueError("agent_intent_too_long")
        if len(self.context_refs) > MAX_ITEMS or len(self.memory_refs) > MAX_ITEMS:
            raise ValueError("agent_reference_limit_exceeded")


@dataclass(frozen=True, slots=True)
class AgentDecision:
    request_id: str
    selected_agent: str | None
    selected_capability: str | None
    selected_model_route: str | None = None
    requires_approval: bool = False
    approval_state: AgentApprovalState = AgentApprovalState.NOT_REQUIRED
    execution_mode: AgentExecutionMode = AgentExecutionMode.PLAN_ONLY
    reason: str = ""
    confidence: float = 0.0
    fallback_agent: str | None = None
    blocked_reason: str | None = None
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("agent_confidence_out_of_range")
        if len(self.reason) > MAX_DESCRIPTION or len(self.blocked_reason or "") > MAX_DESCRIPTION:
            raise ValueError("agent_decision_text_too_long")


@dataclass(frozen=True, slots=True)
class AgentResult:
    request_id: str
    agent_name: str
    capability: str
    status: AgentResultStatus
    output: str = ""
    evidence: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    error: str | None = None
    created_at: str = "phase3"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.output) > MAX_OUTPUT or len(self.error or "") > MAX_DESCRIPTION:
            raise ValueError("agent_result_text_too_long")
        if len(self.evidence) > MAX_ITEMS or len(self.warnings) > MAX_ITEMS:
            raise ValueError("agent_result_items_exceeded")
