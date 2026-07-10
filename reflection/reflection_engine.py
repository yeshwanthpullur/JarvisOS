"""Reflection execution engine."""

from __future__ import annotations

import logging

from reflection.reflection_analyzer import ReflectionAnalyzer
from reflection.reflection_confidence import ReflectionConfidence
from reflection.reflection_context import ReflectionContext
from reflection.reflection_feedback import ReflectionFeedback
from reflection.reflection_improvement import ReflectionImprovement
from reflection.reflection_learning import ReflectionLearning, ReflectionLearningRecord
from reflection.reflection_patterns import ReflectionPatternRecord, ReflectionPatterns
from reflection.reflection_request import ReflectionRequest
from reflection.reflection_response import ReflectionResponse
from reflection.reflection_report import ReflectionReport
from reflection.reflection_validator import ReflectionValidator


class ReflectionEngine:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.analyzer = ReflectionAnalyzer(logger=self.logger)
        self.learning = ReflectionLearning(logger=self.logger)
        self.patterns = ReflectionPatterns(logger=self.logger)
        self.confidence = ReflectionConfidence(logger=self.logger)
        self.improvement = ReflectionImprovement(logger=self.logger)
        self.feedback = ReflectionFeedback(logger=self.logger)
        self.validator = ReflectionValidator(logger=self.logger)
        self.initialized = False

    def initialize(self) -> None:
        self.analyzer.initialize()
        self.learning.initialize()
        self.patterns.initialize()
        self.confidence.initialize()
        self.improvement.initialize()
        self.feedback.initialize()
        self.validator.initialize()
        self.initialized = True
        self.logger.info("reflection_engine_initialized")

    def reflect(self, request: ReflectionRequest, context: ReflectionContext | None = None) -> ReflectionResponse:
        self._ensure_initialized()
        if not self.validator.validate_request(request):
            raise ValueError("Reflection request is invalid.")
        analysis = self.analyzer.analyze(request, context)
        confidence_report = self.confidence.measure(
            expected=float(request.statistics.get("expected_confidence", 0.8)),
            actual=float(request.statistics.get("actual_confidence", 0.7)),
        )
        improvements = self.improvement.generate(
            (
                "decision",
                "planning",
                "reasoning",
                "workflow",
                "retrieval",
                "research",
                "task",
                "conversation",
                "provider",
                "agent",
            )
        )
        self.learning.capture(
            ReflectionLearningRecord(
                learning_id=request.reflection_id,
                kind="reflection",
                description=analysis.summary,
                confidence=confidence_report.actual_confidence,
                metadata=dict(request.metadata),
            )
        )
        for index, item in enumerate(improvements, start=1):
            self.patterns.register(
                ReflectionPatternRecord(
                    pattern_id=f"{request.reflection_id}-{index}",
                    pattern_type=item.category,
                    description=item.recommendation,
                    confidence=item.confidence,
                    metadata=dict(request.metadata),
                )
            )
        report = ReflectionReport(
            summary=analysis.summary,
            success_factors=analysis.success_factors,
            failure_factors=analysis.failure_factors,
            missing_information=analysis.missing_information,
            wrong_assumptions=analysis.wrong_assumptions,
            improvement_opportunities=analysis.improvement_opportunities,
            statistics=dict(request.statistics),
            diagnostics={"confidence": confidence_report.summary},
        )
        response = ReflectionResponse(
            reflection_report=report.summary,
            success_score=1.0 if analysis.success_factors else 0.4,
            failure_score=0.0 if analysis.success_factors else 0.6,
            confidence_score=confidence_report.actual_confidence,
            decision_quality=0.9 if analysis.success_factors else 0.5,
            planning_quality=0.9 if analysis.success_factors else 0.5,
            reasoning_quality=0.9 if analysis.success_factors else 0.5,
            execution_quality=0.9 if analysis.success_factors else 0.5,
            improvement_candidates=tuple(item.recommendation for item in improvements),
            learning_candidates=(analysis.summary,),
            memory_references=tuple(request.metadata.get("memory_references", ())),
            knowledge_references=tuple(request.metadata.get("knowledge_references", ())),
            diagnostics={"analysis": analysis.summary, "confidence": confidence_report.summary},
            statistics={"patterns": len(self.patterns.records)},
            metadata={"report": report},
        )
        if not self.validator.validate_response(response):
            raise ValueError("Reflection response is invalid.")
        self.logger.info("reflection_completed reflection_id=%s", request.reflection_id)
        return response

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReflectionEngine must be initialized before use.")
