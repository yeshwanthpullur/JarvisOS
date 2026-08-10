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


@dataclass(slots=True)
class ResearchAgent:
    enabled: bool = True
    web_available: bool = True
    documents_available: bool = True
    planner: ResearchPlanner = field(default_factory=ResearchPlanner)
    evidence_collector: ResearchEvidenceCollector = field(default_factory=ResearchEvidenceCollector)
    history: list[ResearchResult] = field(default_factory=list)

    def plan(self, query: str, *, depth: ResearchDepth = ResearchDepth.STANDARD) -> ResearchPlan:
        return self.planner.create_plan(query, depth=depth)

    def summarize(self, query: str, evidence: tuple[ResearchEvidence, ...] = (), *, depth: ResearchDepth = ResearchDepth.STANDARD) -> ResearchResult:
        plan = self.plan(query, depth=depth)
        if plan.status is ResearchStatus.BLOCKED:
            result = ResearchResult(str(uuid4()), ResearchStatus.BLOCKED, plan, evidence, None, warnings=plan.warnings, error="blocked_by_policy")
            self.history.append(result)
            return result
        if not evidence:
            summary = ResearchSummary(str(uuid4()), plan.question_id, "Evidence unavailable; this is a plan-only research result.", (), confidence=0.0, limitations=("No evidence retrieved.",), missing_information=("No authoritative evidence was supplied.",))
            result = ResearchResult(str(uuid4()), ResearchStatus.EVIDENCE_ONLY if plan.needs_web or plan.needs_documents else ResearchStatus.PLANNED, plan, (), summary, warnings=("Evidence unavailable.",))
            self.history.append(result)
            return result
        snippets = self.evidence_collector.summarize(evidence)
        answer = " | ".join(snippets)[:1200]
        summary = ResearchSummary(str(uuid4()), plan.question_id, answer, tuple(item.evidence_id for item in evidence[:12]), confidence=min(0.9, max(item.confidence for item in evidence)), limitations=("Summary is bounded and evidence-backed only.",))
        result = ResearchResult(str(uuid4()), ResearchStatus.COMPLETED, plan, evidence[:12], summary, warnings=("Research uses bounded, read-only evidence only.",))
        self.history.append(result)
        return result

    def status(self) -> dict[str, object]:
        plan = self.planner.create_plan("research local models for JARVIS")
        return {
            "enabled": self.enabled,
            "status": "partial" if self.enabled else "disabled",
            "web_available": self.web_available,
            "documents_available": self.documents_available,
            "local_only": True,
            "default_depth": "standard",
            "source_policy": "read_only" if self.web_available else "local_only",
            "research_agent": "partial",
            "last_intent": plan.research_type.value,
        }

    def show(self, request_id: str) -> ResearchResult | None:
        return next((item for item in reversed(self.history) if item.request_id == request_id), None)
