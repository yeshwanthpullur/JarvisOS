"""Safe built-in document ingestion with untrusted evidence metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import hashlib
import re


SECRET_NAMES = {".env", "id_rsa", "id_ed25519", "credentials.json", "secrets.json"}
SECRET_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
SAFE_TEXT_SUFFIXES = {".txt", ".md", ".csv", ".html"}
PLANNED_SUFFIXES = {".pdf", ".docx", ".xlsx", ".pptx", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}
INJECTION = re.compile(r"(?i)(ignore (all|the|previous) instructions|reveal secrets|run (this|the) command|delete memory|upload this file)")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class DocumentChunk:
    chunk_id: str; document_id: str; text: str; page_number: int | None; section_heading: str; source_ref: str; confidence: float; trusted_status: str = "untrusted_user_provided_source"; prompt_injection_detected: bool = False


@dataclass(frozen=True, slots=True)
class DocumentRecord:
    document_id: str; display_name: str; source_type: str; size_bytes: int; parser_used: str; sensitivity_class: str; trusted_status: str; chunks: tuple[DocumentChunk, ...]; extracted_at: str = field(default_factory=_now); status: str = "parsed"; warnings: tuple[str, ...] = ()


class DocumentPipeline:
    def __init__(self, root: Path, *, max_file_bytes: int = 25_000_000, max_pages: int = 100, max_extract_chars: int = 20_000, ocr_enabled: bool = False) -> None:
        self.root = root.resolve(); self.max_file_bytes = max(1, max_file_bytes); self.max_pages = max(1, max_pages); self.max_extract_chars = max(100, max_extract_chars); self.ocr_enabled = ocr_enabled; self.records: dict[str, DocumentRecord] = {}; self.audit: list[dict[str, object]] = []

    def classify(self, path: Path) -> str:
        name = path.name.lower()
        if name in SECRET_NAMES or path.suffix.lower() in SECRET_SUFFIXES or any(token in name for token in ("token", "secret", "credential", "private_key")):
            return "SECRET_OR_CREDENTIAL_FILE"
        if any(token in name for token in ("medical", "health")):
            return "MEDICAL_DOCUMENT"
        if any(token in name for token in ("financial", "bank", "invoice")):
            return "FINANCIAL_DOCUMENT"
        return "PROJECT_DOCUMENT" if self.root in path.resolve().parents else "USER_PRIVATE_DOCUMENT"

    def inspect(self, path_text: str) -> dict[str, object]:
        path = Path(path_text).expanduser().resolve()
        sensitivity = self.classify(path)
        suffix = path.suffix.lower()
        exists = path.is_file()
        size = path.stat().st_size if exists else 0
        supported = suffix in SAFE_TEXT_SUFFIXES or suffix in PLANNED_SUFFIXES
        allowed = exists and supported and size <= self.max_file_bytes and sensitivity != "SECRET_OR_CREDENTIAL_FILE"
        reason = "ready" if allowed else "secret_file_blocked" if sensitivity == "SECRET_OR_CREDENTIAL_FILE" else "file_missing" if not exists else "unsupported_file_type" if not supported else "file_too_large"
        return {"display_name": path.name[:160], "suffix": suffix, "size_bytes": size, "sensitivity": sensitivity, "allowed": allowed, "reason": reason, "path_exposed": False}

    def parse(self, path_text: str) -> DocumentRecord:
        info = self.inspect(path_text); document_id = f"doc-{uuid4().hex[:12]}"
        if not info["allowed"]:
            record = DocumentRecord(document_id, str(info["display_name"]), str(info["suffix"]), int(info["size_bytes"]), "none", str(info["sensitivity"]), "untrusted_user_provided_source", (), status="blocked", warnings=(str(info["reason"]),))
        else:
            path = Path(path_text).expanduser().resolve(); suffix = path.suffix.lower()
            if suffix not in SAFE_TEXT_SUFFIXES:
                warning = "ocr_disabled" if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"} and not self.ocr_enabled else "optional_parser_unavailable"
                record = DocumentRecord(document_id, path.name[:160], suffix, path.stat().st_size, "none", str(info["sensitivity"]), "untrusted_user_provided_source", (), status="degraded", warnings=(warning,))
            else:
                text = path.read_text(encoding="utf-8", errors="replace")[: self.max_extract_chars]
                chunks = self._chunks(document_id, path.name, text)
                record = DocumentRecord(document_id, path.name[:160], suffix, path.stat().st_size, "builtin_text", str(info["sensitivity"]), "untrusted_user_provided_source", chunks, warnings=("document_instructions_are_untrusted",) if any(item.prompt_injection_detected for item in chunks) else ())
        self.records[record.document_id] = record; self.audit.append({"operation": "parse", "document_id": record.document_id, "status": record.status, "parser": record.parser_used, "chunks": len(record.chunks), "at": _now()}); self.audit = self.audit[-100:]
        return record

    def _chunks(self, document_id: str, name: str, text: str) -> tuple[DocumentChunk, ...]:
        output = []
        for index, start in enumerate(range(0, len(text), 1200)):
            value = text[start:start + 1200]
            ref = hashlib.sha256(f"{document_id}:{index}".encode()).hexdigest()[:16]
            output.append(DocumentChunk(f"chunk-{ref}", document_id, value, None, "", f"{name}#chunk-{index + 1}", 1.0, prompt_injection_detected=bool(INJECTION.search(value))))
        return tuple(output[:100])

    def summarize(self, document_id: str) -> str:
        record = self.records.get(document_id)
        if not record or not record.chunks:
            return "Document evidence unavailable; no summary was fabricated."
        text = " ".join(chunk.text for chunk in record.chunks)
        return f"Evidence summary ({record.chunks[0].source_ref}): {text[:1200]}"

    def status(self) -> dict[str, object]:
        return {"builtin_text": True, "docling": "detected_via_tool_registry", "marker": "detected_via_tool_registry", "ocr_enabled": self.ocr_enabled, "automatic_memory_update": False, "automatic_knowledge_update": False, "documents": len(self.records)}
