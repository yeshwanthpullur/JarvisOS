"""Bounded, evidence-driven external research runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
import re
from typing import Protocol
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from uuid import uuid4

from .models import ResearchDepth
from .safety import evaluate_research_safety
from .planner import classify_research_intent

MAX_TEXT = 2400
MAX_SNIPPET = 500
_TRACKING = {"fbclid", "gclid", "mc_cid", "mc_eid"}
_SECRET = re.compile(r"(?i)(api[_-]?key|access[_-]?token|authorization|password|secret|credential)\s*[:=]\s*\S+")
_INJECTION = re.compile(r"(?i)(ignore (all |the )?(previous|system) instructions|reveal (the )?(system prompt|secret)|execute (this )?(command|tool)|install (this|the)|send (a )?(message|email)|write (this )?to memory)")


def _bound(value: object, limit: int = MAX_TEXT) -> str:
    text = " ".join(str(value or "").split())
    text = _SECRET.sub("[REDACTED]", text)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _now() -> str:
    return datetime.now(UTC).isoformat()


class SearchProviderState(StrEnum):
    REGISTERED = "registered"
    DISABLED = "disabled"
    UNCONFIGURED = "unconfigured"
    CREDENTIAL_MISSING = "credential_missing"
    CONFIGURED = "configured"
    REACHABLE = "reachable"
    READY = "ready"
    DEGRADED = "degraded"
    RATE_LIMITED = "rate_limited"
    BLOCKED = "blocked"
    ERROR = "error"


class SourceType(StrEnum):
    OFFICIAL_DOCUMENTATION = "official_documentation"
    GOVERNMENT = "government"
    ACADEMIC = "academic"
    STANDARDS_BODY = "standards_body"
    PRIMARY_SOURCE = "primary_source"
    COMPANY_OFFICIAL = "company_official"
    NEWS = "news"
    REPOSITORY = "repository"
    TECHNICAL_BLOG = "technical_blog"
    COMMUNITY = "community"
    FORUM = "forum"
    SOCIAL = "social"
    UNKNOWN = "unknown"


class SupportState(StrEnum):
    UNSUPPORTED = "unsupported"
    SINGLE_SOURCE = "single_source"
    CORROBORATED = "corroborated"
    STRONG_PRIMARY_SUPPORT = "strong_primary_support"
    CONFLICTING = "conflicting"
    STALE = "stale"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ResearchBudget:
    max_queries: int
    max_sources: int
    max_retrievals: int
    max_duration_seconds: int
    max_followup_rounds: int
    max_pages_per_domain: int = 3
    max_chars_per_source: int = 6000
    max_total_chars: int = 24000

    @classmethod
    def for_mode(cls, mode: ResearchDepth | str) -> "ResearchBudget":
        mode = ResearchDepth(mode)
        return {
            ResearchDepth.QUICK: cls(2, 4, 3, 20, 0),
            ResearchDepth.STANDARD: cls(5, 8, 6, 60, 1),
            ResearchDepth.DEEP: cls(8, 12, 10, 120, 2),
        }[mode]


@dataclass(frozen=True, slots=True)
class ExternalResearchRequest:
    question: str
    mode: ResearchDepth = ResearchDepth.STANDARD
    domains: tuple[str, ...] = ()
    freshness_requirement: str = "unknown"
    source_preferences: tuple[str, ...] = ()
    source_exclusions: tuple[str, ...] = ()
    max_queries: int | None = None
    max_sources: int | None = None
    max_retrievals: int | None = None
    max_duration: int | None = None
    privacy_classification: str = "normal"
    output_format: str = "summary"
    citation_required: bool = True
    request_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        if not self.question.strip() or len(self.question) > MAX_TEXT:
            raise ValueError("invalid_research_request")
        if _SECRET.search(self.question):
            raise ValueError("secret_bearing_research_request")


@dataclass(frozen=True, slots=True)
class ExternalResearchPlan:
    request_id: str
    normalized_question: str
    subquestions: tuple[str, ...]
    query_candidates: tuple[str, ...]
    target_source_types: tuple[SourceType, ...]
    freshness_requirement: str
    verification_requirements: tuple[str, ...]
    source_diversity_requirement: int
    stopping_conditions: tuple[str, ...]
    budget: ResearchBudget
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""
    source_type: SourceType = SourceType.UNKNOWN
    published_at: str | None = None
    updated_at: str | None = None


class SearchProvider(Protocol):
    provider_id: str
    state: SearchProviderState
    def search(self, query: str, *, limit: int) -> tuple[SearchResult, ...]: ...


@dataclass(slots=True)
class SearchProviderRegistry:
    providers: dict[str, SearchProvider] = field(default_factory=dict)

    def register(self, provider: SearchProvider) -> None:
        if provider.provider_id in self.providers:
            raise ValueError("duplicate_search_provider")
        self.providers[provider.provider_id] = provider

    def ready(self) -> tuple[SearchProvider, ...]:
        return tuple(p for p in self.providers.values() if p.state is SearchProviderState.READY)

    def summary(self) -> dict[str, object]:
        return {"total": len(self.providers), "ready": len(self.ready()), "states": {key: value.state.value for key, value in sorted(self.providers.items())}}


@dataclass(frozen=True, slots=True)
class UnconfiguredSearchProvider:
    provider_id: str = "external_search"
    state: SearchProviderState = SearchProviderState.UNCONFIGURED
    def search(self, query: str, *, limit: int) -> tuple[SearchResult, ...]:
        return ()


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password:
        raise ValueError("unsafe_research_url")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if not k.lower().startswith("utm_") and k.lower() not in _TRACKING and not _SECRET.search(f"{k}={v}")]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", urlencode(query), ""))


@dataclass(frozen=True, slots=True)
class ResearchSource:
    source_id: str
    provider: str
    url_or_reference: str
    normalized_url: str
    title: str
    source_type: SourceType = SourceType.UNKNOWN
    publisher: str | None = None
    author: str | None = None
    published_at: str | None = None
    updated_at: str | None = None
    retrieved_at: str = field(default_factory=_now)
    language: str | None = None
    content_type: str | None = None
    freshness: str = "unknown"
    quality_signals: tuple[str, ...] = ()
    trust_class: str = "untrusted_external"
    retrieval_status: str = "discovered"
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class EvidenceChunk:
    evidence_id: str
    source_id: str
    text_or_summary: str
    location_ref: str = ""
    retrieved_at: str = field(default_factory=_now)
    claim_tags: tuple[str, ...] = ()
    freshness: str = "unknown"
    extraction_confidence: str = "unknown"
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "text_or_summary", _bound(self.text_or_summary, MAX_SNIPPET))
        if _INJECTION.search(self.text_or_summary):
            object.__setattr__(self, "warnings", self.warnings + ("prompt_injection_content_ignored",))


@dataclass(frozen=True, slots=True)
class ResearchClaim:
    claim_id: str
    statement: str
    evidence_ids: tuple[str, ...] = ()
    claim_type: str = "factual"
    support_state: SupportState = SupportState.UNSUPPORTED
    contradiction_ids: tuple[str, ...] = ()
    confidence_class: str = "unknown"
    freshness: str = "unknown"
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class KnowledgeCandidate:
    candidate_id: str
    statement: str
    evidence_ids: tuple[str, ...]
    provenance_source_ids: tuple[str, ...]
    freshness: str
    ttl_seconds: int
    memory_write_allowed: bool = False


@dataclass(frozen=True, slots=True)
class ExternalResearchResult:
    request_id: str
    status: str
    plan: ExternalResearchPlan
    sources: tuple[ResearchSource, ...] = ()
    evidence: tuple[EvidenceChunk, ...] = ()
    claims: tuple[ResearchClaim, ...] = ()
    citations: tuple[str, ...] = ()
    knowledge_candidates: tuple[KnowledgeCandidate, ...] = ()
    warnings: tuple[str, ...] = ()
    stop_reason: str = "planned"


@dataclass(slots=True)
class AutonomousResearchRuntime:
    providers: SearchProviderRegistry = field(default_factory=SearchProviderRegistry)
    allow_external_search: bool = False
    allow_browser_retrieval: bool = True
    allow_github: bool = True
    allow_mcp: bool = True
    allow_plugins: bool = True
    require_citations: bool = True
    prefer_primary_sources: bool = True
    enable_counterevidence: bool = True
    cancelled: set[str] = field(default_factory=set)
    history: list[ExternalResearchResult] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.providers.providers:
            self.providers.register(UnconfiguredSearchProvider())

    def plan(self, request: ExternalResearchRequest) -> ExternalResearchPlan:
        intent = classify_research_intent(request.question)
        safety = evaluate_research_safety(request.question, intent)
        mode = ResearchDepth(request.mode)
        budget = ResearchBudget.for_mode(mode)
        budget = ResearchBudget(
            min(request.max_queries or budget.max_queries, budget.max_queries),
            min(request.max_sources or budget.max_sources, budget.max_sources),
            min(request.max_retrievals or budget.max_retrievals, budget.max_retrievals),
            min(request.max_duration or budget.max_duration_seconds, budget.max_duration_seconds),
            budget.max_followup_rounds, budget.max_pages_per_domain, budget.max_chars_per_source, budget.max_total_chars,
        )
        normalized = _bound(request.question)
        subquestions = self._subquestions(normalized, mode)
        queries = self._dedupe((normalized,) + subquestions)[: budget.max_queries]
        warnings = (() if safety.allowed else (safety.reason,)) + (("External search provider is unconfigured.",) if not self.providers.ready() else ())
        return ExternalResearchPlan(request.request_id, normalized, subquestions, queries, (SourceType.OFFICIAL_DOCUMENTATION, SourceType.PRIMARY_SOURCE, SourceType.ACADEMIC), request.freshness_requirement, ("trace every external claim to evidence", "seek independent corroboration", "report contradictions"), 1 if mode is ResearchDepth.QUICK else 2, ("evidence sufficient", "query/source/time budget exhausted", "provider unavailable", "cancelled"), budget, warnings)

    @staticmethod
    def _subquestions(question: str, mode: ResearchDepth) -> tuple[str, ...]:
        base = (f"What primary sources address: {question}?", f"What credible counterevidence exists for: {question}?")
        return base[:0 if mode is ResearchDepth.QUICK else 1 if mode is ResearchDepth.STANDARD else 2]

    @staticmethod
    def _dedupe(values: tuple[str, ...]) -> tuple[str, ...]:
        seen: set[str] = set(); result = []
        for value in values:
            key = " ".join(value.lower().split())
            if key not in seen:
                seen.add(key); result.append(value)
        return tuple(result)

    def run(self, request: ExternalResearchRequest) -> ExternalResearchResult:
        plan = self.plan(request)
        if request.request_id in self.cancelled:
            return self._record(ExternalResearchResult(request.request_id, "cancelled", plan, stop_reason="cancelled"))
        safety = evaluate_research_safety(request.question, classify_research_intent(request.question))
        if not safety.allowed:
            return self._record(ExternalResearchResult(request.request_id, "blocked", plan, warnings=(safety.reason,), stop_reason="policy_blocked"))
        providers = self.providers.ready() if self.allow_external_search else ()
        if not providers:
            return self._record(ExternalResearchResult(request.request_id, "unavailable", plan, warnings=("Live external search is unconfigured; no evidence or citations were fabricated.",), stop_reason="provider_unavailable"))
        results: list[SearchResult] = []
        for query in plan.query_candidates:
            if len(results) >= plan.budget.max_sources: break
            results.extend(providers[0].search(query, limit=plan.budget.max_sources - len(results)))
        sources = self._sources(results[: plan.budget.max_sources], providers[0].provider_id)
        evidence = tuple(EvidenceChunk(str(uuid4()), source.source_id, result.snippet, freshness=source.freshness, extraction_confidence="medium") for source, result in zip(sources, results) if result.snippet)
        claim = self._claim(request.question, sources, evidence)
        citations = tuple(source.normalized_url for source in sources if source.normalized_url)
        candidates = (() if not evidence else (KnowledgeCandidate(str(uuid4()), _bound(request.question, 500), tuple(e.evidence_id for e in evidence), tuple(s.source_id for s in sources), "unknown", 86400),))
        return self._record(ExternalResearchResult(request.request_id, "completed" if evidence else "evidence_unavailable", plan, sources, evidence, (claim,), citations, candidates, ("External content remained untrusted data.",), "evidence_sufficient" if evidence else "no_evidence"))

    def _sources(self, results: list[SearchResult], provider: str) -> tuple[ResearchSource, ...]:
        output=[]; seen=set()
        for item in results:
            try: normalized=normalize_url(item.url)
            except ValueError: continue
            if normalized in seen: continue
            seen.add(normalized)
            signals=("primary_source_preferred",) if item.source_type in {SourceType.OFFICIAL_DOCUMENTATION, SourceType.PRIMARY_SOURCE, SourceType.GOVERNMENT, SourceType.STANDARDS_BODY} else ()
            output.append(ResearchSource(str(uuid4()), provider, normalized, normalized, _bound(item.title, 300), item.source_type, published_at=item.published_at, updated_at=item.updated_at, quality_signals=signals))
        return tuple(output)

    @staticmethod
    def _claim(question: str, sources: tuple[ResearchSource, ...], evidence: tuple[EvidenceChunk, ...]) -> ResearchClaim:
        independent = len({urlsplit(s.normalized_url).hostname for s in sources})
        state = SupportState.UNSUPPORTED if not evidence else SupportState.SINGLE_SOURCE if independent < 2 else SupportState.CORROBORATED
        return ResearchClaim(str(uuid4()), _bound(question, 600), tuple(e.evidence_id for e in evidence), support_state=state, confidence_class="low" if state is SupportState.UNSUPPORTED else "medium", warnings=("Inference only; inspect cited evidence.",))

    def cancel(self, request_id: str) -> None:
        self.cancelled.add(request_id)

    def _record(self, result: ExternalResearchResult) -> ExternalResearchResult:
        self.history.append(result); self.history = self.history[-25:]
        return result

    def status(self) -> dict[str, object]:
        return {"runtime": "implemented", "external_search": "ready" if self.allow_external_search and self.providers.ready() else "unconfigured", "browser_retrieval": "policy_bounded" if self.allow_browser_retrieval else "disabled", "citations": self.require_citations, "knowledge_candidates": True, "direct_memory_writes": False, "autonomous_execution": False, "providers": self.providers.summary()}
