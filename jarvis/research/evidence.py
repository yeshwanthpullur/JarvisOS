"""Bounded evidence collection helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .models import ResearchEvidence, ResearchSourceType


@dataclass(frozen=True, slots=True)
class ResearchEvidenceCollector:
    max_snippet_chars: int = 320

    def summarize(self, evidence: tuple[ResearchEvidence, ...]) -> tuple[str, ...]:
        return tuple(f"{item.source_type.value}:{item.title[:60]}:{item.confidence:.2f}" for item in evidence[:12])

    def from_note(self, title: str, source_ref: str, snippet: str, *, source_type: ResearchSourceType = ResearchSourceType.USER, confidence: float = 0.5) -> ResearchEvidence:
        return ResearchEvidence(
            evidence_id=source_ref or title.lower().replace(" ", "_"),
            source_type=source_type,
            title=title[:120],
            source_ref=source_ref[:200],
            snippet=snippet[: self.max_snippet_chars],
            confidence=confidence,
        )

