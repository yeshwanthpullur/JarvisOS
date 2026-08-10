"""Safe Prime Agent routing and plan-only delegation foundation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from .approvals import requires_approval
from .models import (
    AgentApprovalState,
    AgentCapabilityType,
    AgentDecision,
    AgentExecutionMode,
    AgentResultStatus,
    AgentRiskLevel,
    AgentStatus,
    MAX_DESCRIPTION,
    MAX_INPUT,
    MAX_OUTPUT,
)
from .registry import AgentRegistry


@dataclass(frozen=True, slots=True)
class PrimeRequest:
    user_input: str
    normalized_intent: str = ""
    request_id: str = field(default_factory=lambda: str(uuid4()))
    conversation_context_refs: tuple[str, ...] = ()
    memory_refs: tuple[str, ...] = ()
    preferred_capability: AgentCapabilityType | None = None
    preferred_agent: str | None = None
    preferred_model: str | None = None
    requested_execution_mode: AgentExecutionMode = AgentExecutionMode.PLAN_ONLY
    local_only: bool = True
    created_at: str = "phase3"

    def __post_init__(self) -> None:
        if not self.user_input.strip() or len(self.user_input) > MAX_INPUT:
            raise ValueError("invalid_prime_request")
        if len(self.normalized_intent) > MAX_DESCRIPTION:
            raise ValueError("prime_intent_too_long")


@dataclass(frozen=True, slots=True)
class PrimeDecision:
    request_id: str
    intent: AgentCapabilityType
    selected_agent: str | None
    selected_capability: str | None
    selected_model_route: str | None = None
    risk_level: AgentRiskLevel = AgentRiskLevel.LOW
    approval_required: bool = False
    approval_state: AgentApprovalState = AgentApprovalState.NOT_REQUIRED
    execution_mode: AgentExecutionMode = AgentExecutionMode.PLAN_ONLY
    confidence: float = 0.0
    reason: str = ""
    blocked_reason: str | None = None
    fallback_options: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    candidate_skill: str | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("prime_confidence_out_of_range")
        if len(self.reason) > MAX_DESCRIPTION or len(self.blocked_reason or "") > MAX_DESCRIPTION:
            raise ValueError("prime_decision_text_too_long")


@dataclass(frozen=True, slots=True)
class PrimeExecutionPlan:
    request_id: str
    selected_agent: str | None
    steps: tuple[str, ...]
    plan_id: str = field(default_factory=lambda: str(uuid4()))
    execution_mode: AgentExecutionMode = AgentExecutionMode.PLAN_ONLY
    approval_required: bool = False
    risk_level: AgentRiskLevel = AgentRiskLevel.LOW
    status: AgentResultStatus = AgentResultStatus.PLANNED
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.steps) > 12 or any(len(step) > MAX_DESCRIPTION for step in self.steps):
            raise ValueError("prime_plan_limit_exceeded")


@dataclass(frozen=True, slots=True)
class PrimeResult:
    request_id: str
    decision: PrimeDecision
    execution_plan: PrimeExecutionPlan | None
    result_status: AgentResultStatus
    output: str = ""
    evidence: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    error: str | None = None

    def __post_init__(self) -> None:
        if len(self.output) > MAX_OUTPUT or len(self.error or "") > MAX_DESCRIPTION:
            raise ValueError("prime_result_text_too_long")


_INTENT_TERMS: tuple[tuple[AgentCapabilityType, tuple[str, ...]], ...] = (
    (AgentCapabilityType.ADAPTER, (" mcp", "plugin adapter", "external plugin", "connect github")),
    (AgentCapabilityType.SCHEDULER, ("remind me", "schedule", "tomorrow at", "every hour", "every day", "cron")),
    (AgentCapabilityType.COMMUNICATION, ("instagram", "telegram", "discord", "send email", "send message", "draft an email", "draft email", "post this")),
    (AgentCapabilityType.IMAGE, ("generate an image", "create an image", "image prompt", "picture of")),
    (AgentCapabilityType.VIDEO, ("edit this video", "video edit", "trim video", "video plan")),
    (AgentCapabilityType.VISION, ("analyze image", "describe image", "what is in this image", "vision")),
    (AgentCapabilityType.MEMORY, ("remember", "memory", "recall", "forget")),
    (AgentCapabilityType.WEB, ("search the web", "web page", "webpage", "website", "browse")),
    (AgentCapabilityType.SYNC, ("sync", "queue sync")),
    (AgentCapabilityType.CODING, ("code", "debug", "repository", "repo", "patch", "test suite", "diff", "refactor", "fix the bug")),
    (AgentCapabilityType.DOCUMENTS, ("document", "pdf", "presentation", "summarize this pdf")),
    (AgentCapabilityType.RESEARCH, ("research", "sources", "evidence")),
    (AgentCapabilityType.SYSTEM, ("project status", "system status", "health", "limitations", "hardware")),
    (AgentCapabilityType.DRONE, ("drone", "flight controller", "fly ")),
    (AgentCapabilityType.ROBOTICS, ("robot", "robotics", "motor control", "sensor")),
)


def classify_intent(text: str) -> AgentCapabilityType:
    lowered = f" {text.strip().lower()} "
    if "research" not in lowered and any(term in lowered for term in ("compare vllm", "llama.cpp", "nemotron", "nvidia nim", "model provider")):
        return AgentCapabilityType.SYSTEM
    if "integration" in lowered and any(term in lowered for term in (" add ", " plan ", " implement ")):
        return AgentCapabilityType.CODING
    for intent, terms in _INTENT_TERMS:
        if any(term in lowered for term in terms):
            return intent
    return AgentCapabilityType.CONVERSATION if lowered.strip() else AgentCapabilityType.UNKNOWN


def classify_risk(text: str, intent: AgentCapabilityType | None = None) -> AgentRiskLevel:
    lowered = text.lower()
    intent = intent or classify_intent(text)
    if intent is AgentCapabilityType.DRONE or any(term in lowered for term in ("steal credential", "bypass security", "bypass captcha", "captcha", "read my .env", ".env", "spam this", "100 people", "friend's location", "unlock device")):
        return AgentRiskLevel.CRITICAL
    if any(term in lowered for term in ("post", "send email", "send message", "delete", "purchase", "deploy", "account", "control", "write file", "fix automatically", "commit", "push", "install dependency", "microphone", "camera")):
        return AgentRiskLevel.HIGH
    if any(term in lowered for term in ("inspect file", "process file", "edit video", "generate an image")):
        return AgentRiskLevel.MEDIUM
    return AgentRiskLevel.LOW


_AGENT_FOR_INTENT = {
    AgentCapabilityType.CONVERSATION: "conversation_agent",
    AgentCapabilityType.MEMORY: "memory_agent",
    AgentCapabilityType.VISION: "vision_agent",
    AgentCapabilityType.IMAGE: "image_agent",
    AgentCapabilityType.VIDEO: "video_agent",
    AgentCapabilityType.WEB: "web_agent",
    AgentCapabilityType.SYNC: "sync_agent",
    AgentCapabilityType.RESEARCH: "research_agent",
    AgentCapabilityType.CODING: "coding_agent",
    AgentCapabilityType.DOCUMENTS: "document_agent",
    AgentCapabilityType.SCHEDULER: "scheduler_agent",
    AgentCapabilityType.ADAPTER: "adapter_agent",
    AgentCapabilityType.EVALUATION: "evaluation_agent",
    AgentCapabilityType.COMMUNICATION: "communication_agent",
    AgentCapabilityType.ROBOTICS: "robotics_agent",
    AgentCapabilityType.DRONE: "drone_agent",
    AgentCapabilityType.SYSTEM: "model_agent",
}


class PrimeAgent:
    """Produces safe routing decisions and plans without executing side effects."""

    def __init__(
        self,
        registry: AgentRegistry,
        *,
        model_router: Any | None = None,
        skill_registry: Any | None = None,
        enabled: bool = True,
        max_plan_steps: int = 8,
        block_critical_risk: bool = True,
    ) -> None:
        self.registry = registry
        self.model_router = model_router
        self.skill_registry = skill_registry
        self.enabled = enabled
        self.max_plan_steps = max(1, min(max_plan_steps, 12))
        self.block_critical_risk = block_critical_risk
        self.last_decision: PrimeDecision | None = None

    def route(self, request: PrimeRequest) -> PrimeDecision:
        intent = request.preferred_capability or classify_intent(request.normalized_intent or request.user_input)
        risk = classify_risk(request.user_input, intent)
        preferred_name = request.preferred_agent or _AGENT_FOR_INTENT.get(intent)
        if request.preferred_agent is None and intent is AgentCapabilityType.WEB and any(term in request.user_input.lower() for term in ("webpage", "browser", "page summary", "summarize this web")):
            preferred_name = "browser_agent"
        entry = self.registry.get_agent(preferred_name or "")
        candidates = self.registry.find_by_capability(intent, executable_only=False)
        if entry is None and candidates:
            entry = candidates[0]
        critical_block = self.block_critical_risk and risk is AgentRiskLevel.CRITICAL
        available = bool(entry and entry.enabled and entry.status is AgentStatus.READY)
        approval_required = risk in {AgentRiskLevel.HIGH, AgentRiskLevel.CRITICAL}
        approval_state = AgentApprovalState.REQUIRED if approval_required else AgentApprovalState.NOT_REQUIRED
        blocked_reason = None
        mode = AgentExecutionMode.PLAN_ONLY
        if critical_block:
            mode = AgentExecutionMode.BLOCKED
            blocked_reason = "Critical-risk execution is blocked by Phase 3 policy."
        elif risk is AgentRiskLevel.HIGH and intent is AgentCapabilityType.COMMUNICATION:
            blocked_reason = "External sending/posting is unavailable; communication_agent is draft-only."
        elif not available:
            blocked_reason = entry.reason if entry else "No registered agent supports this request."
        model_route = None
        if self.model_router is not None:
            try:
                model_route = self.model_router.route_for_task(intent.value).route_id
            except Exception:
                model_route = None
        decision = PrimeDecision(
            request.request_id,
            intent,
            entry.name if entry else preferred_name,
            intent.value,
            selected_model_route=model_route,
            risk_level=risk,
            approval_required=approval_required,
            approval_state=approval_state,
            execution_mode=mode,
            confidence=0.9 if available else 0.55 if entry else 0.2,
            reason=(f"Matched {intent.value} intent to the governed agent registry." if entry else "No registry match was available."),
            blocked_reason=blocked_reason,
            fallback_options=tuple(item.name for item in candidates[1:4]),
            warnings=("Routing is advisory and performs no side effects.",),
        )
        self.last_decision = decision
        return decision

    def plan(self, request: PrimeRequest) -> PrimeExecutionPlan:
        decision = self.route(request)
        status = AgentResultStatus.BLOCKED if decision.execution_mode is AgentExecutionMode.BLOCKED else AgentResultStatus.PLANNED
        steps = (
            "Validate the normalized request and applicable safety policy.",
            f"Delegate in plan-only mode to {decision.selected_agent or 'no available agent'}.",
            "Return bounded metadata without executing side effects.",
        )[: self.max_plan_steps]
        return PrimeExecutionPlan(
            request.request_id,
            decision.selected_agent,
            steps,
            execution_mode=decision.execution_mode,
            approval_required=decision.approval_required,
            risk_level=decision.risk_level,
            status=status,
            warnings=decision.warnings,
        )

    def status(self) -> dict[str, object]:
        summary = self.registry.registry_summary()
        return {
            "enabled": self.enabled,
            "status": "ready" if self.enabled else "disabled",
            "default_mode": AgentExecutionMode.PLAN_ONLY.value,
            "approval_enforcement": True,
            "critical_risk_blocked": self.block_critical_risk,
            "registered_agents": summary["total_agents"],
            "routeable_agents": summary["ready_agents"],
            "local_only": True,
        }


def render_prime_command(prime: PrimeAgent, command: str, arguments: tuple[str, ...]) -> str:
    if command == "prime status":
        status = prime.status()
        return "Prime Agent: " + " ".join(f"{key}={str(value).lower() if isinstance(value, bool) else value}" for key, value in status.items())
    text = " ".join(arguments).strip()
    if not text:
        return f"Usage: {command} <request>"
    request = PrimeRequest(text)
    decision = prime.route(request)
    if command == "prime risk":
        return f"Prime risk: level={decision.risk_level.value} approval_required={'yes' if decision.approval_required else 'no'} mode={decision.execution_mode.value}."
    if command == "prime plan":
        plan = prime.plan(request)
        return f"Prime plan: agent={plan.selected_agent or 'none'} status={plan.status.value} mode={plan.execution_mode.value} steps=" + " | ".join(plan.steps)
    if command == "prime explain":
        return f"Prime explanation: intent={decision.intent.value} agent={decision.selected_agent or 'none'} reason={decision.reason} blocked={decision.blocked_reason or 'no'}."
    return (
        f"Prime route: intent={decision.intent.value} agent={decision.selected_agent or 'none'} "
        f"capability={decision.selected_capability or 'none'} risk={decision.risk_level.value} "
        f"mode={decision.execution_mode.value} approval_required={'yes' if decision.approval_required else 'no'} "
        f"available={'no' if decision.blocked_reason else 'yes'}."
    )
