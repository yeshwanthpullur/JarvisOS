"""Retrieval validation."""

from __future__ import annotations

from retrieval.retrieval_request import RetrievalRequest
from retrieval.retrieval_response import RetrievalResponse


class RetrievalValidator:
    initialized = True

    def validate_request(self, request: RetrievalRequest) -> tuple[bool, tuple[str, ...]]:
        issues: list[str] = []
        if not request.request_id:
            issues.append("Request ID is required.")
        if not request.query:
            issues.append("Query is required.")
        return (not issues, tuple(issues))

    def validate_context(self, context: object) -> tuple[bool, tuple[str, ...]]:
        return (context is not None, () if context is not None else ("Context is required.",))

    def validate_sources(self, sources: tuple[str, ...]) -> tuple[bool, tuple[str, ...]]:
        return (bool(sources), () if sources else ("At least one source is required.",))

    def validate_results(self, response: RetrievalResponse) -> tuple[bool, tuple[str, ...]]:
        return (True, ())

    def validate_ranking(self, response: RetrievalResponse) -> tuple[bool, tuple[str, ...]]:
        return (True, ())

    def validate_references(self, response: RetrievalResponse) -> tuple[bool, tuple[str, ...]]:
        return (True, ())

    def validate_confidence(self, confidence: float) -> tuple[bool, tuple[str, ...]]:
        return (0.0 <= confidence <= 1.0, () if 0.0 <= confidence <= 1.0 else ("Confidence must be between 0 and 1.",))

    def validate_metadata(self, metadata: dict[str, object]) -> tuple[bool, tuple[str, ...]]:
        return (True, ())
