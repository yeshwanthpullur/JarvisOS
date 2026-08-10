"""Deterministic research planner and intent classifier."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from .models import (
    ResearchDepth,
    ResearchIntent,
    ResearchPlan,
    ResearchQuestion,
    ResearchRiskLevel,
    ResearchSourceType,
    ResearchStatus,
)
from .safety import evaluate_research_safety, is_research_allowed, research_source_policy


_INTENT_MAP: tuple[tuple[ResearchIntent, tuple[str, ...]], ...] = (
    (ResearchIntent.COMPARISON, ("compare", "versus", " vs ", "difference between")),
    (ResearchIntent.TECHNICAL_RESEARCH, ("model", "architecture", "implementation", "adapter", "framework")),
    (ResearchIntent.REPO_RESEARCH, ("repo", "repository", "codebase", "pull request", "commit")),
    (ResearchIntent.LITERATURE_REVIEW, ("literature", "paper", "papers", "citation", "sources")),
    (ResearchIntent.TROUBLESHOOTING, ("fix", "debug", "error", "broken", "not working")),
    (ResearchIntent.MARKET_RESEARCH, ("market", "pricing", "competitor", "compare providers")),
    (ResearchIntent.PRODUCT_RESEARCH, ("product", "workflow", "feature", "best local models")),
    (ResearchIntent.CITATION_NEEDED, ("cite", "citation needed", "reference")),
    (ResearchIntent.DOCUMENT_QUESTION, ("document", "pdf", "report", "slide", "notes")),
    (ResearchIntent.WEB_QUESTION, ("website", "web", "source", "sources about", "find sources")),
    (ResearchIntent.EXPLANATION, ("what is", "explain", "how does", "why")),
)


def classify_research_intent(query: str) -> ResearchIntent:
    lowered = f" {query.strip().lower()} "
    for intent, tokens in _INTENT_MAP:
        if any(token in lowered for token in tokens):
            return intent
    return ResearchIntent.UNKNOWN


def classify_research_risk(query: str, intent: ResearchIntent) -> ResearchRiskLevel:
    allowed, risk, _ = is_research_allowed(query, intent)
    return ResearchRiskLevel.BLOCKED if not allowed else risk


@dataclass(slots=True)
class ResearchPlanner:
    max_steps: int = 5
    max_evidence_items: int = 5
    max_snippet_chars: int = 320
    max_summary_chars: int = 1200
    save_history: bool = True
    web_available: bool = True
    documents_available: bool = True
    _history: list[ResearchQuestion] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.max_steps = max(1, min(int(self.max_steps), 12))
        self.max_evidence_items = max(1, min(int(self.max_evidence_items), 12))
        self.max_snippet_chars = max(80, min(int(self.max_snippet_chars), 320))
        self.max_summary_chars = max(200, min(int(self.max_summary_chars), 1200))

    def create_question(self, query: str, *, depth: ResearchDepth = ResearchDepth.STANDARD) -> ResearchQuestion:
        normalized = " ".join(query.strip().split())
        intent = classify_research_intent(normalized)
        return ResearchQuestion(query=query, normalized_query=normalized, intent=intent, depth=depth)

    def create_plan(self, query: str, *, depth: ResearchDepth = ResearchDepth.STANDARD) -> ResearchPlan:
        question = self.create_question(query, depth=depth)
        safety = evaluate_research_safety(question.normalized_query, question.intent)
        if not safety.allowed:
            return ResearchPlan(question.question_id, question.normalized_query, question.intent, ("Reject the unsafe request.",), needs_user_clarification=False, risk_level=safety.risk_level, status=ResearchStatus.BLOCKED, warnings=(safety.reason,), depth=depth)
        policy = research_source_policy(web_available=self.web_available, documents_available=self.documents_available)
        steps = self._build_steps(question.intent, depth)[: self.max_steps]
        status = ResearchStatus.PLANNED
        needs_web = policy.allowed_sources and ResearchSourceType.WEB in policy.allowed_sources and question.intent in {ResearchIntent.WEB_QUESTION, ResearchIntent.REPO_RESEARCH, ResearchIntent.LITERATURE_REVIEW, ResearchIntent.TECHNICAL_RESEARCH, ResearchIntent.COMPARISON}
        needs_documents = ResearchSourceType.DOCUMENT in policy.allowed_sources and question.intent in {ResearchIntent.DOCUMENT_QUESTION, ResearchIntent.LITERATURE_REVIEW}
        needs_clarification = question.intent is ResearchIntent.UNKNOWN
        if needs_clarification:
            status = ResearchStatus.NEEDS_CLARIFICATION
        plan = ResearchPlan(
            question.question_id,
            question.normalized_query,
            question.intent,
            steps,
            required_evidence=("authoritative sources", "bounded snippets"),
            allowed_sources=policy.allowed_sources,
            blocked_sources=policy.blocked_sources,
            needs_web=needs_web,
            needs_documents=needs_documents,
            needs_user_clarification=needs_clarification,
            risk_level=safety.risk_level,
            status=status,
            warnings=tuple(filter(None, (
                safety.reason,
                "Action-oriented restricted-domain work requires explicit confirmation." if safety.action_confirmation_required else "",
            ))),
            depth=depth,
        )
        if self.save_history:
            self._history.append(question)
            self._history = self._history[-50:]
        return plan

    def _build_steps(self, intent: ResearchIntent, depth: ResearchDepth) -> tuple[str, ...]:
        base = {
            ResearchIntent.COMPARISON: (
                "Define the comparison scope.",
                "Collect bounded evidence for each side.",
                "Summarize tradeoffs and fit for JARVIS.",
            ),
            ResearchIntent.REPO_RESEARCH: (
                "Inspect repository context and issue history.",
                "Identify relevant files or milestones.",
                "Summarize repo-specific findings.",
            ),
            ResearchIntent.LITERATURE_REVIEW: (
                "Identify authoritative references.",
                "Extract bounded evidence snippets.",
                "Summarize with caveats and citations.",
            ),
            ResearchIntent.DOCUMENT_QUESTION: (
                "Identify the relevant document.",
                "Extract bounded evidence from the document.",
                "Summarize the answer with explicit missing information.",
            ),
            ResearchIntent.WEB_QUESTION: (
                "Confirm the query can be answered read-only.",
                "Collect bounded evidence snippets.",
                "Summarize with source references.",
            ),
        }.get(intent, (
            "Normalize the request.",
            "Identify required evidence.",
            "Draft a bounded summary.",
        ))
        if depth is ResearchDepth.QUICK:
            return base[:2]
        if depth is ResearchDepth.DEEP:
            return base + ("Check for contradictions and limitations.",)
        return base

    def history(self) -> tuple[ResearchQuestion, ...]:
        return tuple(self._history)
