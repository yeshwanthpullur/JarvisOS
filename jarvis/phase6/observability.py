"""Bounded local-only metrics and payload-free tracing."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import perf_counter
from uuid import uuid4
import os
import re


SAFE_NAME = re.compile(r"^[a-zA-Z0-9_.:-]{1,80}$")


@dataclass(frozen=True, slots=True)
class MetricPoint:
    domain: str; name: str; value: float; unit: str; measured: bool; timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True, slots=True)
class TraceSpan:
    trace_id: str; span_id: str; parent_span_id: str; subsystem: str; operation: str; status: str; duration_ms: float; payload_included: bool = False; timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ObservabilityRuntime:
    DOMAINS = {"system","application","provider","model","conversation","voice","browser","research","document","memory","vector","graph","coding","workflow","orchestration","connector","mcp","plugin","security","release"}
    def __init__(self, *, max_metrics: int = 500, max_traces: int = 200) -> None:
        self.metrics = deque(maxlen=max_metrics); self.traces = deque(maxlen=max_traces); self.started = perf_counter(); self.telemetry_upload = False; self.include_payloads = False; self.profiling_enabled = False
    def record(self, domain: str, name: str, value: float, unit: str = "count", *, measured: bool = True) -> MetricPoint:
        if domain not in self.DOMAINS or not SAFE_NAME.match(name) or not SAFE_NAME.match(unit): raise ValueError("invalid_observability_label")
        item = MetricPoint(domain, name, float(value), unit, measured); self.metrics.append(item); return item
    def span(self, subsystem: str, operation: str, duration_ms: float, status: str = "completed", *, trace_id: str = "", parent_span_id: str = "") -> TraceSpan:
        for value in (subsystem, operation, status):
            if not SAFE_NAME.match(value): raise ValueError("invalid_trace_label")
        item = TraceSpan(trace_id or f"trace-{uuid4().hex[:12]}", f"span-{uuid4().hex[:12]}", parent_span_id[:40], subsystem, operation, status, max(0.0, duration_ms), False); self.traces.append(item); return item
    def snapshot(self) -> dict[str, object]:
        self.record("system", "cpu_count", float(os.cpu_count() or 0), "cores")
        self.record("application", "uptime", perf_counter() - self.started, "seconds")
        return {"metrics": len(self.metrics), "traces": len(self.traces), "uptime_seconds": round(perf_counter() - self.started, 3), "telemetry_upload": self.telemetry_upload, "payloads": self.include_payloads, "profiling": self.profiling_enabled, "authority": "informational_only"}
    def domain_summary(self, domain: str) -> dict[str, object]:
        values = tuple(item for item in self.metrics if item.domain == domain)
        return {"domain": domain, "points": len(values), "measured": sum(item.measured for item in values), "estimated": sum(not item.measured for item in values), "latest": tuple(f"{item.name}={item.value}{item.unit}" for item in values[-10:])}
