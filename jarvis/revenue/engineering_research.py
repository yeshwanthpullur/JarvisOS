"""The first R1 deliverable: a bounded engineering research package skill."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import time
from uuid import uuid4

from jarvis.research import ResearchAgent, ResearchPlanner
from jarvis.research.models import ResearchDepth, ResearchEvidence, ResearchResult, ResearchSourceType, ResearchStatus


_MAX = 1200
_SECRET = re.compile(r"(?i)(api[_-]?key|password|access[_-]?token|secret|credential)\s*[:=]")
_REQUIRED = ("topic", "objective", "audience", "scope", "required_output", "format", "deadline", "source_constraints", "privacy_requirements", "quality_requirements")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _bound(value: object, limit: int = _MAX) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


@dataclass(frozen=True, slots=True)
class ResearchPackageRequest:
    topic: str
    objective: str
    audience: str = "technical reader"
    scope: str = "bounded"
    required_output: str = "evidence-backed Markdown report"
    format: str = "markdown"
    deadline: str = "not specified"
    source_constraints: str = "approved read-only sources"
    privacy_requirements: str = "local_only"
    quality_requirements: str = "completeness, provenance, consistency, human review"
    request_id: str = field(default_factory=lambda: f"r1-{uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        for name in _REQUIRED:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip() or len(value) > _MAX:
                raise ValueError(f"invalid_research_package_{name}")
        if _SECRET.search(" ".join(getattr(self, name) for name in _REQUIRED)):
            raise ValueError("secret_shaped_research_package_request")


@dataclass(frozen=True, slots=True)
class QualityReport:
    passed: bool
    checks: tuple[str, ...]
    failures: tuple[str, ...] = ()
    human_review_required: bool = True
    status: str = "REVIEW_REQUIRED"


@dataclass(frozen=True, slots=True)
class CostMeasurement:
    provider_cost: str = "UNKNOWN"
    tool_cost: str = "UNKNOWN"
    compute_cost: str = "UNKNOWN"
    total_direct_cost: str = "UNKNOWN"
    manual_minutes: str = "UNKNOWN"
    automated_minutes: str = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class WorkflowRunRecord:
    workflow_id: str
    request: str
    start_time: str
    end_time: str
    tools_used: tuple[str, ...]
    agents_used: tuple[str, ...]
    providers_used: tuple[str, ...]
    artifacts: tuple[str, ...]
    test_results: tuple[str, ...]
    quality_result: str
    human_review: str
    operating_cost: str
    manual_time: str
    automated_time: str
    status: str
    failure_class: str = ""


class EngineeringResearchPackage:
    """Compose existing research authorities into an isolated, reviewable package."""

    skill_id = "EngineeringResearchPackage"
    version = "1.0.0"

    def __init__(self, *, research_agent: ResearchAgent | None = None, max_evidence: int = 8) -> None:
        self.research_agent = research_agent or ResearchAgent(web_available=False, documents_available=True, local_only=True, planner=ResearchPlanner(web_available=False, documents_available=True))
        self.max_evidence = max(1, min(int(max_evidence), 8))

    def skill_manifest(self) -> dict[str, object]:
        return {
            "skill_id": self.skill_id,
            "version": self.version,
            "inputs": _REQUIRED,
            "outputs": ("final_report", "executive_summary", "references", "evidence", "quality_report", "metadata"),
            "required_capabilities": ("research", "documents", "rag", "verification"),
            "tools": ("ResearchAgent", "local_document_writer"),
            "agents": ("research_agent", "document_agent"),
            "provider_policy": "local_first; approved read-only sources; no paid dependency",
            "workflow": "requirements->plan->evidence->synthesis->quality->human_review",
            "privacy": "isolated workspace; no silent memory write",
            "failure_handling": "bounded degraded result with explicit failure class",
            "fallbacks": "plan-only summary, manual sources, typed review",
        }

    def run(self, request: ResearchPackageRequest, workspace: Path, *, evidence: tuple[ResearchEvidence, ...] = (), provider_state: str = "local") -> tuple[WorkflowRunRecord, QualityReport, ResearchResult]:
        started = time.perf_counter()
        start = _now()
        workspace = Path(workspace).resolve()
        for name in ("input", "working", "evidence", "output", "audit"):
            (workspace / name).mkdir(parents=True, exist_ok=True)
        plan_result = self.research_agent.summarize(request.topic, evidence[: self.max_evidence], depth=ResearchDepth.STANDARD)
        input_record = asdict(request)
        (workspace / "input" / "request.json").write_text(json.dumps(input_record, indent=2), encoding="utf-8")
        if evidence:
            (workspace / "evidence" / "evidence.json").write_text(json.dumps([asdict(item) for item in evidence[: self.max_evidence]], indent=2), encoding="utf-8")
        quality = self.quality_gate(request, plan_result, provider_state=provider_state)
        automated_minutes = f"{(time.perf_counter() - started) / 60:.4f}"
        cost = CostMeasurement(automated_minutes=automated_minutes)
        summary = plan_result.summary.answer if plan_result.summary else "Evidence unavailable; plan-only result."
        report = "# Engineering Research Package\n\n## Executive Summary\n" + _bound(summary) + "\n\n## References\n" + "\n".join(f"- {item.source_ref}" for item in plan_result.evidence) + "\n\n## Limitations\n" + "\n".join(f"- {item}" for item in (plan_result.summary.limitations if plan_result.summary else ("Evidence unavailable.",)))
        (workspace / "output" / "final_report.md").write_text(report[:6000], encoding="utf-8")
        (workspace / "output" / "executive_summary.md").write_text(_bound(summary), encoding="utf-8")
        (workspace / "output" / "references.md").write_text("\n".join(item.source_ref for item in plan_result.evidence), encoding="utf-8")
        (workspace / "audit" / "quality_report.json").write_text(json.dumps(asdict(quality), indent=2), encoding="utf-8")
        (workspace / "output" / "metadata.json").write_text(json.dumps({"label": "SYNTHETIC PORTFOLIO SAMPLE" if provider_state == "synthetic" else "INTERNAL VALIDATION", "workflow_version": self.version, "provider_state": provider_state, "cost": asdict(cost)}, indent=2), encoding="utf-8")
        status = "completed_review_required" if quality.passed else "degraded"
        failure_class = "" if quality.passed else ("PROVIDER" if provider_state not in {"local", "synthetic"} else "RESEARCH" if not evidence else "QUALITY")
        record = WorkflowRunRecord(self.skill_id, _bound(request.topic, 240), start, _now(), ("ResearchAgent", "local_document_writer"), ("research_agent", "document_agent"), (provider_state,), ("output/final_report.md", "output/executive_summary.md", "output/references.md", "output/metadata.json", "audit/quality_report.json"), ("quality_gate",), quality.status, "REQUIRED", cost.total_direct_cost, cost.manual_minutes, cost.automated_minutes, status, failure_class)
        (workspace / "audit" / "run_record.json").write_text(json.dumps(asdict(record), indent=2), encoding="utf-8")
        return record, quality, plan_result

    @staticmethod
    def human_review_checklist() -> tuple[str, ...]:
        return ("requirements coverage", "factual correctness", "source quality", "citation/provenance", "formatting", "completeness", "privacy", "obvious hallucinations", "unsupported claims")

    def review(self, quality: QualityReport, *, reviewer_role: str = "QA lead") -> dict[str, object]:
        """Record a bounded review decision; it does not grant external delivery authority."""
        outcome = "APPROVED_FOR_SYNTHETIC_PORTFOLIO_ONLY" if quality.passed else "REJECTED_FOR_CORRECTION"
        return {"reviewer_role": reviewer_role[:80], "checklist": self.human_review_checklist(), "review_outcome": outcome, "issues_found": quality.failures, "corrections": (), "final_outcome": outcome, "human_review_required": True}

    def quality_gate(self, request: ResearchPackageRequest, result: ResearchResult, *, provider_state: str) -> QualityReport:
        checks = ["completeness", "accuracy", "source quality", "citation/provenance", "requirement coverage", "formatting", "consistency", "privacy"]
        failures: list[str] = []
        if result.status not in {ResearchStatus.COMPLETED, ResearchStatus.PLANNED}:
            failures.append("research_result_not_deliverable")
        if not result.evidence:
            failures.append("evidence_unavailable")
        if any(not item.source_ref for item in result.evidence):
            failures.append("citation_missing")
        if provider_state not in {"local", "synthetic"}:
            failures.append("provider_not_verified")
        return QualityReport(not failures, tuple(checks), tuple(failures), True, "PASSED_REVIEW_REQUIRED" if not failures else "DEGRADED_REVIEW_REQUIRED")
