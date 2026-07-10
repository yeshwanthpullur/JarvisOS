"""Research execution architecture."""

from __future__ import annotations

import logging

from research.knowledge_builder import KnowledgeBuilder
from research.learning_engine import LearningEngine
from research.research_context import ResearchContext
from research.research_request import ResearchRequest
from research.research_response import ResearchResponse
from research.research_planner import ResearchPlanner
from research.research_summarizer import ResearchSummarizer
from research.research_validator import ResearchValidator


class ResearchEngine:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self.planner = ResearchPlanner(logger=self._logger)
        self.summarizer = ResearchSummarizer(logger=self._logger)
        self.knowledge_builder = KnowledgeBuilder(logger=self._logger)
        self.learning_engine = LearningEngine(logger=self._logger)
        self.validator = ResearchValidator(logger=self._logger)
        self.initialized = False

    def initialize(self) -> None:
        self.planner.initialize()
        self.summarizer.initialize()
        self.knowledge_builder.initialize()
        self.learning_engine.initialize()
        self.validator.initialize()
        self.initialized = True
        self._logger.info("research_engine_initialized")

    def execute(self, request: ResearchRequest, context: ResearchContext | None = None) -> ResearchResponse:
        self._ensure_initialized()
        if not self.validator.validate_request(request):
            raise ValueError("Research request is invalid.")
        plan = self.planner.build_plan(request)
        findings = (f"Research findings for {request.topic}",)
        knowledge_updates = self.knowledge_builder.prepare_updates(findings)
        summary = self.summarizer.summarize(
            ResearchResponse(findings=findings, summary=f"Summary for {request.topic}", references=("ref-1",))
        )
        learning_plan = self.learning_engine.build_learning_plan(request.topic)
        self._logger.info("research_executed topic=%s", request.topic)
        return ResearchResponse(
            findings=findings,
            summary=summary["executive_summary"],
            references=("ref-1",),
            learning_plan={"plan": learning_plan, "knowledge_updates": knowledge_updates, "research_plan": plan},
            confidence=0.75,
            metadata=dict(request.metadata),
        )

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ResearchEngine must be initialized before use.")
