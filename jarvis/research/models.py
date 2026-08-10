"""Typed, bounded research models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import PurePath, PureWindowsPath
import re
from uuid import uuid4


MAX_TEXT = 1200
MAX_SNIPPET = 320
MAX_ITEMS = 12


class ResearchIntent(StrEnum):
    EXPLANATION = "explanation"
    COMPARISON = "comparison"
    TECHNICAL_RESEARCH = "technical_research"
    PROJECT_RESEARCH = "project_research"
    REPO_RESEARCH = "repo_research"
    LITERATURE_REVIEW = "literature_review"
    TROUBLESHOOTING = "troubleshooting"
    MARKET_RESEARCH = "market_research"
    PRODUCT_RESEARCH = "product_research"
    CITATION_NEEDED = "citation_needed"
    DOCUMENT_QUESTION = "document_question"
    WEB_QUESTION = "web_question"
    UNKNOWN = "unknown"


class ResearchDepth(StrEnum):
    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class ResearchRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


class ResearchStatus(StrEnum):
    PLANNED = "planned"
    NEEDS_CLARIFICATION = "needs_clarification"
    EVIDENCE_ONLY = "evidence_only"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"


class ResearchSourceType(StrEnum):
    WEB = "web"
    DOCUMENT = "document"
    PROJECT = "project"
    MEMORY = "memory"
    USER = "user"
    UNKNOWN = "unknown"


def _bounded(value: object, limit: int) -> str:
    text = str(value or "").strip()
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _is_absolute_ref(value: str) -> bool:
    return PurePath(value).is_absolute() or PureWindowsPath(value).is_absolute()


_SECRET_PATTERN = re.compile(r"(?i)(api[_-]?key|password|access[_-]?token|secret|authorization|credential)\s*[:=]\s*\S+")


def _contains_secret(value: str) -> bool:
    return bool(_SECRET_PATTERN.search(value))


@dataclass(frozen=True, slots=True)
class ResearchQuestion:
    query: str
    normalized_query: str
    intent: ResearchIntent = ResearchIntent.UNKNOWN
    scope: str = ""
    depth: ResearchDepth = ResearchDepth.STANDARD
    question_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        if not self.query.strip() or len(self.query) > MAX_TEXT:
            raise ValueError("invalid_research_question")
        if len(self.normalized_query) > MAX_TEXT or len(self.scope) > MAX_TEXT:
            raise ValueError("research_question_text_too_long")


@dataclass(frozen=True, slots=True)
class ResearchPlan:
    question_id: str
    query: str
    research_type: ResearchIntent
    steps: tuple[str, ...]
    required_evidence: tuple[str, ...] = ()
    allowed_sources: tuple[ResearchSourceType, ...] = (ResearchSourceType.WEB, ResearchSourceType.DOCUMENT, ResearchSourceType.PROJECT)
    blocked_sources: tuple[ResearchSourceType, ...] = ()
    needs_web: bool = False
    needs_documents: bool = False
    needs_user_clarification: bool = False
    risk_level: ResearchRiskLevel = ResearchRiskLevel.LOW
    status: ResearchStatus = ResearchStatus.PLANNED
    warnings: tuple[str, ...] = ()
    plan_id: str = field(default_factory=lambda: str(uuid4()))
    depth: ResearchDepth = ResearchDepth.STANDARD

    def __post_init__(self) -> None:
        if not self.query or len(self.query) > MAX_TEXT:
            raise ValueError("invalid_research_plan_query")
        if not self.steps or len(self.steps) > MAX_ITEMS or any(len(step) > MAX_TEXT for step in self.steps):
            raise ValueError("research_plan_too_large")


@dataclass(frozen=True, slots=True)
class ResearchEvidence:
    evidence_id: str
    source_type: ResearchSourceType
    title: str
    source_ref: str
    snippet: str
    confidence: float = 0.0
    retrieved_at: str = field(default_factory=_now)
    metadata: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("research_evidence_confidence_out_of_range")
        if len(self.snippet) > MAX_SNIPPET or len(self.title) > MAX_TEXT or len(self.source_ref) > MAX_TEXT:
            raise ValueError("research_evidence_text_too_long")
        if _is_absolute_ref(self.source_ref):
            raise ValueError("private_source_ref_not_allowed")
        if _contains_secret(self.source_ref) or _contains_secret(self.snippet):
            raise ValueError("secret_shaped_research_evidence_not_allowed")
        if any(str(key).lower() in {"secret", "token", "password", "credential", "authorization", "api_key", "access_token"} for key in self.metadata):
            raise ValueError("secret_research_metadata_not_allowed")
        if len(self.metadata) > MAX_ITEMS or any(len(str(key)) > 80 or len(str(value)) > MAX_SNIPPET for key, value in self.metadata.items()):
            raise ValueError("research_evidence_metadata_too_large")


@dataclass(frozen=True, slots=True)
class ResearchSummary:
    summary_id: str
    question_id: str
    answer: str
    evidence_refs: tuple[str, ...] = ()
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    created_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("research_summary_confidence_out_of_range")
        if len(self.answer) > MAX_TEXT:
            raise ValueError("research_summary_too_long")


@dataclass(frozen=True, slots=True)
class ResearchResult:
    request_id: str
    status: ResearchStatus
    plan: ResearchPlan | None
    evidence: tuple[ResearchEvidence, ...] = ()
    summary: ResearchSummary | None = None
    warnings: tuple[str, ...] = ()
    error: str | None = None
    created_at: str = field(default_factory=_now)

    def __post_init__(self) -> None:
        if len(self.evidence) > MAX_ITEMS or len(self.warnings) > MAX_ITEMS or len(self.error or "") > MAX_TEXT:
            raise ValueError("research_result_too_large")
