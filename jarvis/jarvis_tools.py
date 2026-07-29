"""Governed Tool Intelligence owned by Executive JARVIS."""

from __future__ import annotations

import ast
import json
import logging
import operator
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from threading import Event, Lock
from time import monotonic
from typing import Any, Callable, Mapping
from uuid import uuid4


class ToolRiskClass(StrEnum):
    MINIMAL = "minimal"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ToolMode(StrEnum):
    OFF = "off"
    CONFIRM = "confirm"
    AUTOMATIC_SAFE = "automatic-safe"
    AUTOMATIC = "automatic"


class ToolStatus(StrEnum):
    READY = "ready"
    AWAITING_APPROVAL = "awaiting_approval"
    RUNNING = "running"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    TIMED_OUT = "timed_out"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"
    REJECTED = "rejected"
    INVALID_OUTPUT = "invalid_output"


@dataclass(frozen=True, slots=True)
class ToolLimits:
    maximum_per_request: int = 3
    maximum_per_coordination: int = 6
    maximum_retries: int = 1
    maximum_timeout_seconds: int = 30
    maximum_concurrent: int = 2
    maximum_output_bytes: int = 64_000
    maximum_argument_bytes: int = 16_000
    maximum_chained_depth: int = 1
    maximum_dry_run_seconds: int = 5
    maximum_history: int = 200


@dataclass(frozen=True, slots=True)
class JarvisToolRecord:
    """Validated tool definition; implementations are never serialized."""

    tool_id: str
    name: str
    capabilities: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ("tool.execute",)
    metadata: dict[str, object] = field(default_factory=dict)
    description: str = ""
    version: str = "1.0"
    input_schema: Mapping[str, object] = field(default_factory=dict)
    output_schema: Mapping[str, object] = field(default_factory=dict)
    risk_class: ToolRiskClass = ToolRiskClass.MINIMAL
    mutation_type: str = "none"
    side_effect_type: str = "none"
    approval_policy: str = "policy"
    timeout_seconds: int = 10
    retry_limit: int = 0
    enabled: bool = True
    healthy: bool = True
    available: bool = True
    lifecycle_state: str = "active"
    implementation: Callable[[dict[str, object]], object] | None = field(default=None, compare=False, repr=False)


@dataclass(frozen=True, slots=True)
class ToolNeedAssessment:
    requires_tool: bool
    reason: str
    requested_capability: str | None = None
    candidate_tool_types: tuple[str, ...] = ()
    risk_class: ToolRiskClass = ToolRiskClass.MINIMAL
    mutation_expected: bool = False
    external_side_effect_expected: bool = False
    credentials_required: bool = False
    approval_required: bool = False
    confidence: float = 0.0
    fallback_available: bool = True
    estimated_cost_class: str = "none"
    estimated_latency_class: str = "low"
    arguments: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolSelection:
    selected_tool_id: str | None
    selection_reason: str
    rejected_candidates: tuple[tuple[str, str], ...] = ()
    capability_match_score: float = 0.0
    permission_status: str = "unknown"
    approval_status: str = "unknown"
    health_status: str = "unknown"
    risk_class: ToolRiskClass = ToolRiskClass.MINIMAL
    fallback_tools: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ToolInvocationRequest:
    invocation_id: str
    parent_request_id: str
    tool_id: str
    operation: str
    arguments: dict[str, object]
    validated_arguments: dict[str, object]
    permission_scope: tuple[str, ...]
    risk_class: ToolRiskClass
    timeout: int
    retry_limit: int
    execution_policy: str
    dry_run: bool = False
    approval_reference: str | None = None
    coordination_id: str | None = None
    workflow_id: str | None = None
    task_id: str | None = None
    idempotency_key: str | None = None
    audit_metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolExecutionPlan:
    decision: str
    request: ToolInvocationRequest | None
    expected_side_effects: tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True, slots=True)
class ToolResult:
    invocation_id: str
    parent_request_id: str
    tool_id: str
    operation: str
    status: ToolStatus
    content: str = ""
    structured_data: dict[str, object] = field(default_factory=dict)
    output_schema_valid: bool = True
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    side_effects: tuple[str, ...] = ()
    affected_resources: tuple[str, ...] = ()
    rollback_available: bool = False
    started_at: str = ""
    completed_at: str = ""
    latency: float = 0.0
    retry_count: int = 0
    cancellation_status: str = "not_requested"
    coordination_id: str | None = None
    workflow_id: str | None = None
    task_id: str | None = None

    @property
    def success(self) -> bool:
        return self.status == ToolStatus.COMPLETED


class JarvisTools:
    """Authoritative registry and governed preparation/execution facade."""

    _SECRET_NAMES = {"password", "secret", "token", "api_key", "authorization", "credential"}

    def __init__(self, storage_dir: Path | None = None, logger: logging.Logger | None = None, limits: ToolLimits | None = None) -> None:
        self._tools: dict[str, JarvisToolRecord] = {}
        self._history: list[ToolResult] = []
        self._active: dict[str, Event] = {}
        self._request_counts: dict[str, int] = {}
        self._lock = Lock()
        self.limits = limits or ToolLimits()
        self.mode = ToolMode.AUTOMATIC_SAFE
        self.logger = logger or logging.getLogger("tool_intelligence")
        self.storage_dir = storage_dir
        self.initialized = True
        self.register_safe_builtins()

    def register(self, record: JarvisToolRecord) -> None:
        self._validate_definition(record)
        if record.tool_id in self._tools:
            raise ValueError(f"Tool already registered: {record.tool_id}")
        self._tools[record.tool_id] = record
        self.logger.info("tool_registered tool_id=%s risk_class=%s", record.tool_id, record.risk_class.value)

    def register_safe_builtins(self) -> None:
        self.register(JarvisToolRecord(
            "core.calculator", "Safe calculator", ("calculate", "arithmetic"),
            description="Deterministic local arithmetic", input_schema={"type": "object", "required": ["expression"], "additionalProperties": False, "properties": {"expression": {"type": "string", "maxLength": 256}}},
            output_schema={"type": "object", "required": ["result"]}, implementation=_calculate,
        ))
        self.register(JarvisToolRecord(
            "core.text_transform", "Text transformer", ("text_transform",),
            description="Deterministic local text transformation", input_schema={"type": "object", "required": ["text", "operation"], "additionalProperties": False, "properties": {"text": {"type": "string", "maxLength": 4096}, "operation": {"type": "string", "enum": ["upper", "lower", "title"]}}},
            output_schema={"type": "object", "required": ["result"]}, implementation=_transform_text,
        ))

    def lookup(self, tool_id: str) -> JarvisToolRecord | None:
        return self._tools.get(tool_id)

    def list_tools(self) -> tuple[JarvisToolRecord, ...]:
        return tuple(self._tools.values())

    def assess(self, content: str) -> ToolNeedAssessment:
        text = content.strip()
        lowered = text.lower()
        calculation = re.search(r"(?:calculate|compute|what is)\s+([0-9().+\-*/%\s]+)\??$", lowered)
        if calculation:
            return ToolNeedAssessment(True, "deterministic arithmetic is requested", "calculate", ("calculator",), confidence=0.98, arguments={"expression": calculation.group(1).strip()})
        transform = re.match(r"(?:make|convert|transform)\s+(.+?)\s+(?:to\s+)?(uppercase|lowercase|title case)$", text, re.I)
        if transform:
            operation = {"uppercase": "upper", "lowercase": "lower", "title case": "title"}[transform.group(2).lower()]
            return ToolNeedAssessment(True, "deterministic text transformation is requested", "text_transform", ("transformation",), confidence=0.96, arguments={"text": transform.group(1), "operation": operation})
        return ToolNeedAssessment(False, "a provider-only answer is sufficient", confidence=0.9)

    def match(self, capability: str, granted_permissions: tuple[str, ...] = ("tool.execute",)) -> ToolSelection:
        rejected: list[tuple[str, str]] = []
        compatible: list[JarvisToolRecord] = []
        for tool in self._tools.values():
            reason = None
            if capability not in tool.capabilities:
                continue
            if not tool.enabled or tool.lifecycle_state != "active": reason = "disabled"
            elif not tool.available: reason = "unavailable"
            elif not tool.healthy: reason = "unhealthy"
            elif not set(tool.permissions).issubset(granted_permissions): reason = "permission_denied"
            if reason: rejected.append((tool.tool_id, reason))
            else: compatible.append(tool)
        if not compatible:
            return ToolSelection(None, "no compatible permitted tool", tuple(rejected))
        compatible.sort(key=lambda item: (list(ToolRiskClass).index(item.risk_class), item.tool_id))
        selected = compatible[0]
        return ToolSelection(selected.tool_id, "capability, health, permission, and lowest-risk match", tuple(rejected), 1.0, "granted", "policy", "healthy", selected.risk_class, tuple(item.tool_id for item in compatible[1:]))

    def prepare(self, parent_request_id: str, tool_id: str, operation: str, arguments: Mapping[str, object], *, permissions: tuple[str, ...] = ("tool.execute",), approval_reference: str | None = None, dry_run: bool = False, coordination_id: str | None = None, workflow_id: str | None = None, task_id: str | None = None, chain_depth: int = 0) -> ToolExecutionPlan:
        tool = self.lookup(tool_id)
        if tool is None: return ToolExecutionPlan("blocked", None, reason="missing_tool")
        if chain_depth > self.limits.maximum_chained_depth: return ToolExecutionPlan("blocked", None, reason="chained_depth_exceeded")
        if self.mode == ToolMode.OFF: return ToolExecutionPlan("blocked", None, reason="tool_mode_off")
        if not tool.enabled or not tool.available or not tool.healthy: return ToolExecutionPlan("blocked", None, reason="tool_unavailable")
        if not set(tool.permissions).issubset(permissions): return ToolExecutionPlan("blocked", None, reason="permission_denied")
        try: validated = self.validate_arguments(tool, arguments)
        except ValueError as exc: return ToolExecutionPlan("require_clarification", None, reason=str(exc))
        approval_needed = self.mode == ToolMode.CONFIRM or tool.risk_class in {ToolRiskClass.HIGH, ToolRiskClass.CRITICAL} or tool.mutation_type != "none"
        request = ToolInvocationRequest(str(uuid4()), parent_request_id, tool_id, operation, dict(arguments), validated, permissions, tool.risk_class, min(tool.timeout_seconds, self.limits.maximum_timeout_seconds), min(tool.retry_limit, self.limits.maximum_retries), self.mode.value, dry_run, approval_reference, coordination_id, workflow_id, task_id, str(uuid4()) if tool.mutation_type != "none" else None)
        if approval_needed and not approval_reference: return ToolExecutionPlan("require_approval", request, (tool.side_effect_type,), "explicit approval required")
        return ToolExecutionPlan("ready_for_execution", request, (tool.side_effect_type,) if tool.side_effect_type != "none" else (), "validated")

    def validate_arguments(self, tool: JarvisToolRecord, arguments: Mapping[str, object]) -> dict[str, object]:
        try: encoded = json.dumps(arguments)
        except (TypeError, ValueError) as exc: raise ValueError("arguments_not_serializable") from exc
        if len(encoded.encode()) > self.limits.maximum_argument_bytes: raise ValueError("arguments_too_large")
        if any(str(key).lower() in self._SECRET_NAMES for key in arguments): raise ValueError("secret_argument_rejected")
        schema = tool.input_schema
        properties = dict(schema.get("properties", {})) if isinstance(schema, Mapping) else {}
        required = tuple(schema.get("required", ())) if isinstance(schema, Mapping) else ()
        missing = [key for key in required if key not in arguments]
        if missing: raise ValueError("missing_arguments:" + ",".join(missing))
        if schema.get("additionalProperties") is False:
            unknown = set(arguments) - set(properties)
            if unknown: raise ValueError("unknown_arguments:" + ",".join(sorted(unknown)))
        validated: dict[str, object] = {}
        for key, value in arguments.items():
            rule = properties.get(key, {})
            expected = rule.get("type")
            if expected == "string" and not isinstance(value, str): raise ValueError(f"invalid_type:{key}")
            if expected == "number" and not isinstance(value, (int, float)): raise ValueError(f"invalid_type:{key}")
            if isinstance(value, str) and len(value) > int(rule.get("maxLength", len(value))): raise ValueError(f"value_too_large:{key}")
            if "enum" in rule and value not in rule["enum"]: raise ValueError(f"invalid_enum:{key}")
            if rule.get("format") == "path" and (".." in Path(str(value)).parts or Path(str(value)).is_absolute()): raise ValueError(f"unsafe_path:{key}")
            if rule.get("format") == "url" and not re.match(r"^https?://", str(value)): raise ValueError(f"unsafe_url:{key}")
            validated[key] = value
        return validated

    def execute(self, plan: ToolExecutionPlan, *, executive_approved: bool = False) -> ToolResult:
        if plan.decision != "ready_for_execution" or plan.request is None:
            return self._failure(plan.request, ToolStatus.BLOCKED, plan.reason or plan.decision)
        request = plan.request
        if not executive_approved: return self._failure(request, ToolStatus.REJECTED, "executive_approval_required")
        tool = self.lookup(request.tool_id)
        if tool is None or tool.implementation is None: return self._failure(request, ToolStatus.FAILED, "tool_implementation_unavailable")
        with self._lock:
            if len(self._active) >= self.limits.maximum_concurrent: return self._failure(request, ToolStatus.BLOCKED, "concurrency_limit")
            count = self._request_counts.get(request.parent_request_id, 0)
            if count >= self.limits.maximum_per_request: return self._failure(request, ToolStatus.BLOCKED, "request_invocation_limit")
            self._request_counts[request.parent_request_id] = count + 1
            self._active[request.invocation_id] = Event()
        if request.dry_run:
            result = ToolResult(request.invocation_id, request.parent_request_id, request.tool_id, request.operation, ToolStatus.COMPLETED, "Dry run validated; no action was performed.", {"validated_arguments": request.validated_arguments, "expected_side_effects": plan.expected_side_effects}, started_at=_now(), completed_at=_now(), coordination_id=request.coordination_id, workflow_id=request.workflow_id, task_id=request.task_id)
            return self._finish(result)
        started, clock = _now(), monotonic()
        self.logger.info("tool_execution_started request_id=%s invocation_id=%s tool_id=%s operation=%s risk_class=%s", request.parent_request_id, request.invocation_id, request.tool_id, request.operation, request.risk_class.value)
        try:
            pool = ThreadPoolExecutor(max_workers=1)
            future = pool.submit(tool.implementation, request.validated_arguments)
            try:
                raw = future.result(timeout=request.timeout)
            finally:
                pool.shutdown(wait=False, cancel_futures=True)
            cancel = self._active[request.invocation_id]
            if cancel.is_set(): return self._finish(ToolResult(request.invocation_id, request.parent_request_id, request.tool_id, request.operation, ToolStatus.CANCELLED, errors=("cancelled",), started_at=started, completed_at=_now(), latency=monotonic()-clock, cancellation_status="cancelled"))
            data = raw if isinstance(raw, dict) else {"result": raw}
            content = str(data.get("result", raw))
            if len(content.encode()) > self.limits.maximum_output_bytes: return self._finish(self._failure(request, ToolStatus.INVALID_OUTPUT, "output_too_large"))
            required = tuple(tool.output_schema.get("required", ()))
            if any(key not in data for key in required): return self._finish(self._failure(request, ToolStatus.INVALID_OUTPUT, "output_schema_mismatch"))
            result = ToolResult(request.invocation_id, request.parent_request_id, request.tool_id, request.operation, ToolStatus.COMPLETED, content, data, started_at=started, completed_at=_now(), latency=monotonic()-clock, coordination_id=request.coordination_id, workflow_id=request.workflow_id, task_id=request.task_id)
            self.logger.info("tool_result_normalized request_id=%s invocation_id=%s tool_id=%s execution_status=completed", request.parent_request_id, request.invocation_id, request.tool_id)
            return self._finish(result)
        except FutureTimeout:
            return self._finish(self._failure(request, ToolStatus.TIMED_OUT, "timeout", started, monotonic()-clock))
        except Exception as exc:
            return self._finish(self._failure(request, ToolStatus.FAILED, type(exc).__name__, started, monotonic()-clock))

    def cancel(self, invocation_id: str) -> bool:
        event = self._active.get(invocation_id)
        if event is None: return False
        event.set(); return True

    def history(self) -> tuple[ToolResult, ...]: return tuple(reversed(self._history))
    def invocation(self, invocation_id: str) -> ToolResult | None: return next((item for item in self._history if item.invocation_id == invocation_id), None)
    def set_mode(self, mode: str) -> ToolMode: self.mode = ToolMode(mode); return self.mode
    def statistics(self) -> dict[str, int | str]: return {"tools": len(self._tools), "active": len(self._active), "history": len(self._history), "mode": self.mode.value}

    def _validate_definition(self, record: JarvisToolRecord) -> None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,63}", record.tool_id): raise ValueError("invalid_tool_id")
        if not record.name.strip(): raise ValueError("tool_name_required")
        if record.implementation is not None and not record.capabilities: raise ValueError("tool_capabilities_required")
        if record.timeout_seconds <= 0: raise ValueError("invalid_timeout")
        if record.risk_class == ToolRiskClass.CRITICAL and record.approval_policy == "never": raise ValueError("unsafe_critical_tool")

    def _failure(self, request: ToolInvocationRequest | None, status: ToolStatus, reason: str, started: str = "", latency: float = 0.0) -> ToolResult:
        return ToolResult(request.invocation_id if request else "", request.parent_request_id if request else "", request.tool_id if request else "", request.operation if request else "", status, errors=(reason,), started_at=started or _now(), completed_at=_now(), latency=latency, coordination_id=request.coordination_id if request else None, workflow_id=request.workflow_id if request else None, task_id=request.task_id if request else None)

    def _finish(self, result: ToolResult) -> ToolResult:
        with self._lock:
            self._active.pop(result.invocation_id, None)
            self._history.append(result)
            self._history = self._history[-self.limits.maximum_history:]
        if self.storage_dir:
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            safe = [{k: v for k, v in asdict(item).items() if k not in {"structured_data"}} for item in self._history]
            (self.storage_dir / "history.json").write_text(json.dumps(safe, default=str, indent=2), encoding="utf-8")
        return result


def _now() -> str: return datetime.now(UTC).isoformat()


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}


def _calculate(arguments: dict[str, object]) -> dict[str, object]:
    def evaluate(node: ast.AST, depth: int = 0) -> float | int:
        if depth > 12: raise ValueError("expression_too_complex")
        if isinstance(node, ast.Expression): return evaluate(node.body, depth + 1)
        if isinstance(node, ast.Constant) and type(node.value) in {int, float}: return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS: return _OPS[type(node.op)](evaluate(node.left, depth + 1), evaluate(node.right, depth + 1))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS: return _OPS[type(node.op)](evaluate(node.operand, depth + 1))
        raise ValueError("unsupported_expression")
    return {"result": evaluate(ast.parse(str(arguments["expression"]), mode="eval"))}


def _transform_text(arguments: dict[str, object]) -> dict[str, object]:
    text, operation = str(arguments["text"]), str(arguments["operation"])
    return {"result": {"upper": str.upper, "lower": str.lower, "title": str.title}[operation](text)}
