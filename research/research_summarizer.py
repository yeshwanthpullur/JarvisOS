"""Research summarization architecture."""

from __future__ import annotations

import logging

from research.research_response import ResearchResponse


class ResearchSummarizer:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self._logger.info("research_summarizer_initialized")

    def summarize(self, response: ResearchResponse) -> dict[str, object]:
        self._ensure_initialized()
        return {
            "executive_summary": response.summary,
            "key_findings": response.findings,
            "important_references": response.references,
            "open_questions": (),
            "future_research": (),
            "recommended_actions": (),
        }

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ResearchSummarizer must be initialized before use.")
