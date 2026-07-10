"""Adaptive intelligence engine."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from adaptive.adaptive_context import AdaptiveContext
from adaptive.adaptive_experience import AdaptiveExperience
from adaptive.adaptive_feedback import AdaptiveFeedback
from adaptive.adaptive_learning_queue import AdaptiveLearningQueue, AdaptiveQueueEntry, AdaptiveQueueState
from adaptive.adaptive_policy import AdaptivePolicy
from adaptive.adaptive_request import AdaptiveRequest
from adaptive.adaptive_response import AdaptiveResponse
from adaptive.adaptive_rules import AdaptiveRules
from adaptive.adaptive_validator import AdaptiveValidator


@dataclass(frozen=True, slots=True)
class AdaptiveDecision:
    recommendation: str
    improvement: float
    risk: float
    confidence: float


class AdaptiveEngine:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.experience = AdaptiveExperience()
        self.policy = AdaptivePolicy()
        self.rules = AdaptiveRules()
        self.queue = AdaptiveLearningQueue()
        self.feedback = AdaptiveFeedback()
        self.validator = AdaptiveValidator()
        self.initialized = False

    def initialize(self) -> None:
        self.experience.initialize()
        self.policy  # config only
        self.rules.initialize()
        self.queue.initialize()
        self.feedback.initialize()
        self.validator.initialize()
        self.initialized = True
        self.logger.info("adaptive_engine_initialized")

    def adapt(self, request: AdaptiveRequest, context: AdaptiveContext | None = None) -> AdaptiveResponse:
        self._ensure_initialized()
        if not self.validator.validate_request(request):
            raise ValueError("Adaptive request is invalid.")
        confidence = max(0.0, min(1.0, request.confidence))
        improvement = 0.8 if confidence >= self.policy.confidence_threshold else 0.3
        risk = 0.2 if confidence >= self.policy.confidence_threshold else 0.5
        recommendation = "approve" if self.policy.validate(confidence, risk) else "review"
        candidate = AdaptiveDecision(
            recommendation=recommendation,
            improvement=improvement,
            risk=risk,
            confidence=confidence,
        )
        self.queue.enqueue(
            AdaptiveQueueEntry(
                entry_id=request.adaptive_id,
                adaptive_id=request.adaptive_id,
                state=AdaptiveQueueState.APPROVED if recommendation == "approve" else AdaptiveQueueState.DEFERRED,
                priority=int(improvement * 10),
                metadata=dict(request.context),
            )
        )
        response = AdaptiveResponse(
            adaptation_report=f"Adaptive review for {request.goal or request.intent}.",
            adaptation_candidates=(candidate.recommendation,),
            confidence=confidence,
            estimated_improvement=improvement,
            estimated_risk=risk,
            executive_recommendation="Executive review required",
            memory_references=tuple(request.context.get("memory_references", ())),
            knowledge_references=tuple(request.context.get("knowledge_references", ())),
            diagnostics={"policy": "executive approval required"},
            statistics={"queue_length": len(self.queue.entries)},
        )
        if not self.validator.validate_response(response):
            raise ValueError("Adaptive response is invalid.")
        self.logger.info("adaptive_completed adaptive_id=%s", request.adaptive_id)
        return response

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("AdaptiveEngine must be initialized before use.")
