"""Research agent foundation."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from .evidence import ResearchEvidenceCollector
from .models import (
    ResearchDepth,
    ResearchEvidence,
    ResearchIntent,
    ResearchPlan,
    ResearchResult,
    ResearchRiskLevel,
    ResearchSourceType,
    ResearchStatus,
    ResearchSummary,
)
from .planner import ResearchPlanner, classify_research_intent
from .storage import ResearchHistoryRecord, ResearchHistoryStore
from .runtime import AutonomousResearchRuntime, ExternalResearchRequest


@dataclass(slots=True)
class ResearchAgent:
    enabled: bool = True
    web_available: bool = True
    documents_available: bool = True
    planner: ResearchPlanner = field(default_factory=ResearchPlanner)
    evidence_collector: ResearchEvidenceCollector = field(default_factory=ResearchEvidenceCollector)
    history_store: ResearchHistoryStore | None = None
    local_only: bool = True
    external_search_api_enabled: bool = False
    require_citations_for_web_claims: bool = True
    default_depth: ResearchDepth | str = ResearchDepth.STANDARD
    max_results: int = 50
    last_history_error: str | None = None
    history: list[ResearchResult] = field(default_factory=list)
    runtime: AutonomousResearchRuntime = field(default_factory=AutonomousResearchRuntime)

    def __post_init__(self) -> None:
        self.max_results = max(1, min(int(self.max_results), 100))
        self.default_depth = ResearchDepth(self.default_depth)

    def _record(self, result: ResearchResult) -> ResearchResult:
        self.history.append(result)
        self.history = self.history[-self.max_results :]
        if self.history_store is not None and self.planner.save_history:
            try:
                records = self.history_store.load() + (
                    ResearchHistoryRecord(
                        request_id=result.request_id,
                        intent=result.plan.research_type.value if result.plan else ResearchIntent.UNKNOWN.value,
                        status=result.status.value,
                        evidence_count=len(result.evidence),
                        created_at=result.created_at,
                    ),
                )
                self.history_store.save(records)
                self.last_history_error = None
            except (OSError, ValueError, TypeError):
                self.last_history_error = "RESEARCH_HISTORY_WRITE_FAILED"
        return result

    def plan(self, query: str, *, depth: ResearchDepth | None = None) -> ResearchPlan:
        depth = depth or self.default_depth
        if not self.enabled:
            question = self.planner.create_question(query, depth=depth)
            return ResearchPlan(
                question.question_id,
                question.normalized_query,
                question.intent,
                ("Enable the local Research Agent before planning.",),
                status=ResearchStatus.UNAVAILABLE,
                warnings=("Research Agent is disabled.",),
                depth=depth,
            )
        return self.planner.create_plan(query, depth=depth)

    def plan_result(self, query: str, *, depth: ResearchDepth | None = None) -> ResearchResult:
        plan = self.plan(query, depth=depth)
        error = "blocked_by_policy" if plan.status is ResearchStatus.BLOCKED else "research_disabled" if plan.status is ResearchStatus.UNAVAILABLE else None
        return self._record(
            ResearchResult(
                request_id=str(uuid4()),
                status=plan.status,
                plan=plan,
                warnings=plan.warnings,
                error=error,
            )
        )

    def summarize(self, query: str, evidence: tuple[ResearchEvidence, ...] = (), *, depth: ResearchDepth | None = None) -> ResearchResult:
        plan = self.plan(query, depth=depth)
        if plan.status is ResearchStatus.BLOCKED:
            result = ResearchResult(str(uuid4()), ResearchStatus.BLOCKED, plan, evidence, None, warnings=plan.warnings, error="blocked_by_policy")
            return self._record(result)
        if plan.status is ResearchStatus.UNAVAILABLE:
            return self._record(ResearchResult(str(uuid4()), ResearchStatus.UNAVAILABLE, plan, error="research_disabled"))
        if self.require_citations_for_web_claims and any(
            item.source_type is ResearchSourceType.WEB and not item.source_ref.strip()
            for item in evidence
        ):
            return self._record(
                ResearchResult(
                    str(uuid4()),
                    ResearchStatus.UNAVAILABLE,
                    plan,
                    warnings=("Web evidence requires a bounded source reference.",),
                    error="web_evidence_missing_source_ref",
                )
            )
        if not evidence:
            summary = ResearchSummary(str(uuid4()), plan.question_id, "Evidence unavailable; this is a plan-only research result.", (), confidence=0.0, limitations=("No evidence retrieved.",), missing_information=("No authoritative evidence was supplied.",))
            result = ResearchResult(str(uuid4()), ResearchStatus.PLANNED, plan, (), summary, warnings=("Evidence unavailable.",))
            return self._record(result)
        bounded_evidence = evidence[: self.planner.max_evidence_items]
        snippets = self.evidence_collector.summarize(bounded_evidence)
        answer = " | ".join(snippets)[: self.planner.max_summary_chars]
        summary = ResearchSummary(str(uuid4()), plan.question_id, answer, tuple(item.evidence_id for item in bounded_evidence), confidence=min(0.9, max(item.confidence for item in bounded_evidence)), limitations=("Summary is bounded and evidence-backed only.",))
        result = ResearchResult(str(uuid4()), ResearchStatus.COMPLETED, plan, bounded_evidence, summary, warnings=("Research uses bounded, read-only evidence only.",))
        return self._record(result)

    def status(self) -> dict[str, object]:
        return {
            "enabled": self.enabled,
            "status": "partial" if self.enabled else "disabled",
            "web_read_only_available": self.web_available,
            "documents_available": self.documents_available,
            "local_only": self.local_only,
            "external_search_api": "disabled" if not self.external_search_api_enabled else "enabled",
            "citations_required_for_web": self.require_citations_for_web_claims,
            "default_depth": self.default_depth.value,
            "source_policy": "read_only" if self.web_available else "local_only",
            "research_agent": "partial",
            "history_status": "error" if self.last_history_error else "ready" if self.planner.save_history else "disabled",
            "last_intent": self.history[-1].plan.research_type.value if self.history and self.history[-1].plan else ResearchIntent.UNKNOWN.value,
            "external_runtime": self.runtime.status()["runtime"],
            "live_search": self.runtime.status()["external_search"],
            "direct_memory_writes": False,
        }

    def external(self, query: str, *, mode: ResearchDepth | str = ResearchDepth.STANDARD):
        return self.runtime.run(ExternalResearchRequest(query, ResearchDepth(mode)))

    def show(self, request_id: str) -> ResearchResult | None:
        return next((item for item in reversed(self.history) if item.request_id == request_id), None)

    def history_records(self) -> tuple[ResearchHistoryRecord, ...]:
        if self.history_store is not None:
            return self.history_store.load()
        return tuple(
            ResearchHistoryRecord(
                request_id=item.request_id,
                intent=item.plan.research_type.value if item.plan else ResearchIntent.UNKNOWN.value,
                status=item.status.value,
                evidence_count=len(item.evidence),
                created_at=item.created_at,
            )
            for item in self.history[-self.max_results :]
        )
