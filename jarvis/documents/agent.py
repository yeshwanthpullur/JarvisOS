"""Safe local Document Intelligence planner and bounded text parser."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from jarvis.foundation_common import bounded, contains_secret, new_id, safe_ref
from .models import *
from .pipeline import DocumentIntelligenceRuntime

SAFE_TEXT_TYPES = (".txt", ".md", ".json", ".csv", ".yaml", ".yml")
PLANNED_TYPES = (".pdf", ".docx", ".xlsx", ".pptx")


def classify_document_intent(text: str) -> DocumentIntent:
    value = text.lower()
    if "question" in value or "ask" in value: return DocumentIntent.DOCUMENT_QUESTION_ANSWERING
    if "extract" in value: return DocumentIntent.DOCUMENT_EXTRACTION
    if "compare" in value: return DocumentIntent.DOCUMENT_COMPARISON
    if "citation" in value: return DocumentIntent.CITATION_EXTRACTION
    if "table" in value: return DocumentIntent.TABLE_EXTRACTION_PLAN
    if "ocr" in value or "scan" in value: return DocumentIntent.IMAGE_OR_OCR_PLAN
    if "metadata" in value or "inspect" in value: return DocumentIntent.DOCUMENT_METADATA
    if "summar" in value: return DocumentIntent.DOCUMENT_SUMMARY
    return DocumentIntent.UNKNOWN


def document_safety(text: str) -> tuple[DocumentRiskLevel, bool, str]:
    value = text.lower()
    if contains_secret(text) or any(term in value for term in ("recursive scan", "steal", "private id")):
        return DocumentRiskLevel.CRITICAL, False, "Sensitive, secret, or bulk private-document access is blocked."
    if any(term in value for term in ("medical", "legal", "financial", "bulk", "folder")):
        return DocumentRiskLevel.HIGH, False, "Sensitive or bulk document handling requires a future approval path."
    return DocumentRiskLevel.LOW, True, "Explicit bounded local document use is allowed."


@dataclass(slots=True)
class DocumentAgent:
    root: Path
    enabled: bool = True
    max_file_bytes: int = 1_000_000
    max_extract_chars: int = 4000
    max_history_items: int = 25
    history: list[DocumentResult] = field(default_factory=list)
    runtime: DocumentIntelligenceRuntime = field(init=False)

    def __post_init__(self) -> None:
        self.runtime = DocumentIntelligenceRuntime(self.root, max_file_bytes=self.max_file_bytes, max_extract_chars=self.max_extract_chars)

    def _record(self, result: DocumentResult) -> DocumentResult:
        self.history = (self.history + [result])[-self.max_history_items:]
        return result

    def status(self) -> dict[str, object]:
        pipeline=self.runtime.status(); return {"status":"ready_text_only" if self.enabled else "disabled", "canonical_pipeline":"ready_foundation" if self.enabled else "disabled", "mode":"plan_only", "local_only":True, "text_extraction":True, "pdf_office":"builtin_verified_optional_adapters_unavailable", "ocr":"adapter_unavailable" if not any(x["state"]=="ready" for x in pipeline["ocr"]["local"]) else "ready", "cloud_parsing":"disabled", "docling":next(x["state"] for x in pipeline["parsers"] if x["parser"]=="docling"), "marker":next(x["state"] for x in pipeline["parsers"] if x["parser"]=="marker")}

    def plan(self, request: str) -> DocumentResult:
        risk, allowed, reason = document_safety(request)
        req = DocumentRequest(request, " ".join(request.lower().split()), classify_document_intent(request), risk_level=risk)
        status = DocumentStatus.PLANNED if allowed else DocumentStatus.BLOCKED
        plan = DocumentPlan(req.request_id, req.intent, "Plan bounded document work without hidden ingestion.", ("Validate explicit document reference.", "Apply file-type and size policy.", "Return bounded evidence or an honest unavailable state."), risk_level=risk, approval_required=risk in {DocumentRiskLevel.HIGH, DocumentRiskLevel.CRITICAL}, status=status, warnings=(() if allowed else (reason,)))
        return self._record(DocumentResult(req.request_id, status, req, plan, warnings=plan.warnings, error=None if allowed else "blocked_by_document_policy"))

    def _resolve(self, value: str) -> tuple[Path | None, str | None]:
        if contains_secret(value): return None, "DOCUMENT_SECRET_REFERENCE_BLOCKED"
        candidate = Path(value)
        path = candidate if candidate.is_absolute() else self.root / candidate
        try: resolved = path.resolve(strict=True)
        except (OSError, RuntimeError): return None, "DOCUMENT_NOT_FOUND"
        if not resolved.is_file(): return None, "DOCUMENT_NOT_FILE"
        return resolved, None

    def inspect(self, value: str) -> DocumentResult:
        path, error = self._resolve(value)
        request_id = new_id()
        if error: return self._record(DocumentResult(request_id, DocumentStatus.UNAVAILABLE, error=error))
        assert path is not None
        suffix = path.suffix.lower(); size = path.stat().st_size
        supported = suffix in SAFE_TEXT_TYPES and size <= self.max_file_bytes
        reference = DocumentReference(new_id(), path.name, "explicit_local_file", suffix or "unknown", "small" if size < 100_000 else "bounded", True, supported, (() if supported else ("Parser unavailable or file exceeds the configured limit.",)))
        return self._record(DocumentResult(request_id, DocumentStatus.INSPECTED, references=(reference,), warnings=reference.warnings))

    def extract(self, value: str) -> DocumentResult:
        path, error = self._resolve(value); request_id = new_id()
        if error: return self._record(DocumentResult(request_id, DocumentStatus.UNAVAILABLE, error=error))
        assert path is not None
        if path.suffix.lower() not in SAFE_TEXT_TYPES:
            if path.suffix.lower() == ".pdf" and not path.read_bytes()[:4] == b"%PDF":
                return self._record(DocumentResult(request_id, DocumentStatus.UNAVAILABLE, error="DOCUMENT_PARSER_UNAVAILABLE", warnings=("The PDF signature is invalid or no safe parser can read it.",)))
            try: document=self.runtime.ingest(str(path))
            except ValueError as exc: return self._record(DocumentResult(request_id, DocumentStatus.UNAVAILABLE, error=str(exc).upper()[:240]))
            text="\n".join(item.text for item in document.blocks); preview=bounded(text,self.max_extract_chars)
            extraction=DocumentExtraction(new_id(),document.document_id,DocumentStatus.EXTRACTED,preview,len(text),len(document.pages) or None,document.provenance[-1].backend if document.provenance else "unknown",tuple(document.provenance[-1].warnings if document.provenance else ()))
            return self._record(DocumentResult(request_id,DocumentStatus.EXTRACTED,extraction=extraction,warnings=extraction.warnings))
        if path.stat().st_size > self.max_file_bytes: return self._record(DocumentResult(request_id, DocumentStatus.BLOCKED, error="DOCUMENT_TOO_LARGE"))
        try: text = path.read_text(encoding="utf-8", errors="replace")
        except OSError: return self._record(DocumentResult(request_id, DocumentStatus.FAILED, error="DOCUMENT_READ_FAILED"))
        preview = bounded(text.replace("\x00", " "), self.max_extract_chars)
        if contains_secret(preview): preview = "[content withheld: secret-shaped value detected]"
        extraction = DocumentExtraction(new_id(), new_id(), DocumentStatus.EXTRACTED, preview, len(text), None, "safe_text", ("Output is a bounded preview; content is not persisted.",))
        return self._record(DocumentResult(request_id, DocumentStatus.EXTRACTED, extraction=extraction, warnings=extraction.warnings))

    def summarize(self, value: str, instruction: str = "") -> DocumentResult:
        result = self.extract(value)
        if result.extraction is None: return result
        text = result.extraction.extracted_text_preview
        lines = [line.strip() for line in text.splitlines() if line.strip()][:5]
        summary = DocumentSummary(result.extraction.document_id, bounded(" | ".join(lines) or "No readable text was found."), (result.extraction.extraction_id,), .55, ("Extractive local summary; no model or cloud parser was called.",))
        return self._record(DocumentResult(new_id(), DocumentStatus.COMPLETED, extraction=result.extraction, summary=summary))

    def ask(self, value: str, question: str) -> DocumentResult:
        result = self.extract(value)
        if result.extraction is None: return result
        answer = DocumentQuestionAnswer(result.extraction.document_id, bounded(question), "A bounded extract is available, but semantic document Q&A requires a configured local model route.", (result.extraction.extraction_id,), .2, ("Plan-only semantic Q&A foundation.",), ("No model-backed answer was produced.",))
        return self._record(DocumentResult(new_id(), DocumentStatus.PLANNED, extraction=result.extraction, answer=answer))

    def show(self, job_id: str) -> DocumentResult | None:
        return next((item for item in reversed(self.history) if item.request_id == job_id), None)
