"""Typed models for bounded local Document Intelligence."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from jarvis.foundation_common import new_id, now, validate_items, validate_request_text, validate_text


class DocumentIntent(StrEnum):
    DOCUMENT_SUMMARY = "document_summary"
    DOCUMENT_QUESTION_ANSWERING = "document_question_answering"
    DOCUMENT_EXTRACTION = "document_extraction"
    DOCUMENT_METADATA = "document_metadata"
    DOCUMENT_COMPARISON = "document_comparison"
    DOCUMENT_REWRITE_PLAN = "document_rewrite_plan"
    CITATION_EXTRACTION = "citation_extraction"
    TABLE_EXTRACTION_PLAN = "table_extraction_plan"
    IMAGE_OR_OCR_PLAN = "image_or_ocr_plan"
    REPO_DOCUMENTATION_REVIEW = "repo_documentation_review"
    RESUME_OR_PROFILE_REVIEW = "resume_or_profile_review"
    ACADEMIC_DOCUMENT_REVIEW = "academic_document_review"
    UNKNOWN = "unknown"


class DocumentRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DocumentStatus(StrEnum):
    PLANNED = "planned"
    INSPECTED = "inspected"
    EXTRACTED = "extracted"
    COMPLETED = "completed"
    NEEDS_APPROVAL = "needs_approval"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class DocumentRequest:
    request: str
    normalized_request: str
    intent: DocumentIntent = DocumentIntent.UNKNOWN
    scope: str = "single_document"
    risk_level: DocumentRiskLevel = DocumentRiskLevel.LOW
    request_id: str = field(default_factory=new_id)
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        validate_request_text(self.request); validate_request_text(self.normalized_request); validate_text(self.scope, required=False, limit=120)


@dataclass(frozen=True, slots=True)
class DocumentReference:
    document_id: str
    display_name: str
    source_type: str
    file_type: str
    size_category: str
    approved_for_read: bool
    content_available: bool
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_text(self.display_name, limit=240); validate_items(self.warnings)


@dataclass(frozen=True, slots=True)
class DocumentExtraction:
    extraction_id: str
    document_id: str
    status: DocumentStatus
    extracted_text_preview: str
    text_length: int
    page_count: int | None
    parser_used: str
    warnings: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate_text(self.extracted_text_preview, required=False); validate_items(self.warnings)


@dataclass(frozen=True, slots=True)
class DocumentPlan:
    request_id: str
    intent: DocumentIntent
    summary: str
    proposed_steps: tuple[str, ...]
    required_documents: tuple[str, ...] = ()
    required_permissions: tuple[str, ...] = ("read_explicit_document",)
    supported_file_types: tuple[str, ...] = (".txt", ".md", ".json", ".csv", ".yaml", ".yml")
    unsupported_file_types: tuple[str, ...] = ()
    risk_level: DocumentRiskLevel = DocumentRiskLevel.LOW
    approval_required: bool = False
    status: DocumentStatus = DocumentStatus.PLANNED
    warnings: tuple[str, ...] = ()
    plan_id: str = field(default_factory=new_id)

    def __post_init__(self) -> None:
        validate_text(self.summary); validate_items(self.proposed_steps); validate_items(self.required_documents); validate_items(self.warnings)


@dataclass(frozen=True, slots=True)
class DocumentSummary:
    document_id: str
    summary: str
    evidence_refs: tuple[str, ...] = ()
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    summary_id: str = field(default_factory=new_id)
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        validate_text(self.summary); validate_items(self.evidence_refs)
        if not 0 <= self.confidence <= 1: raise ValueError("document_confidence_out_of_range")


@dataclass(frozen=True, slots=True)
class DocumentQuestionAnswer:
    document_id: str
    question: str
    answer: str
    evidence_refs: tuple[str, ...] = ()
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    answer_id: str = field(default_factory=new_id)
    created_at: str = field(default_factory=now)

    def __post_init__(self) -> None:
        validate_text(self.question); validate_text(self.answer); validate_items(self.evidence_refs)
        if not 0 <= self.confidence <= 1: raise ValueError("document_confidence_out_of_range")


@dataclass(frozen=True, slots=True)
class DocumentResult:
    request_id: str
    status: DocumentStatus
    request: DocumentRequest | None = None
    plan: DocumentPlan | None = None
    references: tuple[DocumentReference, ...] = ()
    extraction: DocumentExtraction | None = None
    summary: DocumentSummary | None = None
    answer: DocumentQuestionAnswer | None = None
    warnings: tuple[str, ...] = ()
    error: str | None = None

    def __post_init__(self) -> None:
        validate_items(self.references); validate_items(self.warnings); validate_text(self.error or "", required=False, limit=240)
