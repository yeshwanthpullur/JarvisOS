"""Source lifecycle, conflict preservation, and citation provenance."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import StrEnum
import json
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from .runtime import EvidenceChunk, ResearchClaim, ResearchSource, SourceType, SupportState, normalize_url


class SourceLifecycle(StrEnum):
    DISCOVERED = "discovered"
    RETRIEVED = "retrieved"
    VERIFIED = "verified"
    CITED = "cited"


@dataclass(frozen=True, slots=True)
class SourceVerification:
    source_id: str
    lifecycle: SourceLifecycle
    authority: str
    freshness: str
    relevance: float
    independence_domain: str
    extraction_confidence: float
    verified: bool
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CitationReference:
    citation_id: str
    source_id: str
    evidence_id: str
    url: str
    title: str
    accessed_at: str
    claim_id: str = ""


class SourceVerifier:
    PRIMARY = {SourceType.OFFICIAL_DOCUMENTATION, SourceType.GOVERNMENT, SourceType.ACADEMIC, SourceType.STANDARDS_BODY, SourceType.PRIMARY_SOURCE, SourceType.COMPANY_OFFICIAL}

    def verify(self, source: ResearchSource, evidence: tuple[EvidenceChunk, ...]) -> SourceVerification:
        linked = tuple(item for item in evidence if item.source_id == source.source_id and item.text_or_summary)
        retrieved = source.retrieval_status in {"retrieved", "verified", "cited"}
        authority = "primary_or_authoritative" if source.source_type in self.PRIMARY else "secondary_or_unknown"
        confidence = 0.8 if linked and source.source_type in self.PRIMARY else 0.6 if linked else 0.0
        verified = bool(retrieved and linked)
        return SourceVerification(source.source_id, SourceLifecycle.VERIFIED if verified else SourceLifecycle.RETRIEVED if retrieved else SourceLifecycle.DISCOVERED, authority, source.freshness, 0.7 if linked else 0.0, urlsplit(source.normalized_url).hostname or "unknown", confidence, verified, () if verified else ("retrieved evidence required",))

    def cite(self, source: ResearchSource, evidence: EvidenceChunk, *, claim_id: str = "") -> CitationReference:
        verification = self.verify(source, (evidence,))
        if not verification.verified or evidence.source_id != source.source_id:
            raise ValueError("unverified_source_cannot_be_cited")
        return CitationReference(f"citation-{uuid4().hex[:12]}", source.source_id, evidence.evidence_id, normalize_url(source.normalized_url), source.title, datetime.now(UTC).isoformat(), claim_id)

    @staticmethod
    def conflicts(claims: tuple[ResearchClaim, ...]) -> tuple[ResearchClaim, ...]:
        return tuple(item for item in claims if item.support_state is SupportState.CONFLICTING or item.contradiction_ids)


class CitationStore:
    def __init__(self, path: Path | None = None, max_items: int = 200) -> None:
        self.path = path; self.max_items = max(1, min(max_items, 1000)); self.items: dict[str, CitationReference] = {}
        if path and path.exists(): self._load()

    def add(self, citation: CitationReference) -> CitationReference:
        self.items[citation.citation_id] = citation
        while len(self.items) > self.max_items: self.items.pop(next(iter(self.items)))
        self._flush(); return citation

    def list(self) -> tuple[CitationReference, ...]: return tuple(self.items.values())
    def _flush(self) -> None:
        if not self.path: return
        self.path.parent.mkdir(parents=True, exist_ok=True); temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"schema_version": 1, "citations": [asdict(item) for item in self.items.values()]}, sort_keys=True), encoding="utf-8"); temporary.replace(self.path)
    def _load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8")); assert raw.get("schema_version") == 1
            for item in raw.get("citations", ())[:self.max_items]:
                citation = CitationReference(**item); self.items[citation.citation_id] = citation
        except (OSError, ValueError, TypeError, AssertionError) as exc: raise ValueError("invalid_citation_store") from exc
