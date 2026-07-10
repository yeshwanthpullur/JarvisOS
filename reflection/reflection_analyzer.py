"""Analysis helpers for reflection."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from reflection.reflection_context import ReflectionContext
from reflection.reflection_request import ReflectionRequest
from reflection.reflection_report import ReflectionReport


@dataclass(slots=True)
class ReflectionAnalysis:
    summary: str
    success_factors: tuple[str, ...]
    failure_factors: tuple[str, ...]
    missing_information: tuple[str, ...]
    wrong_assumptions: tuple[str, ...]
    improvement_opportunities: tuple[str, ...]


class ReflectionAnalyzer:
    def __init__(self, logger: logging.Logger | None = None) -> None:
        self.logger = logger or logging.getLogger(__name__)
        self.initialized = False

    def initialize(self) -> None:
        self.initialized = True
        self.logger.info("reflection_analyzer_initialized")

    def analyze(self, request: ReflectionRequest, context: ReflectionContext | None = None) -> ReflectionAnalysis:
        self._ensure_initialized()
        expected = request.expected_outcome.strip().lower()
        actual = request.actual_outcome.strip().lower()
        success = expected and expected in actual
        failure = expected and not success
        missing_information = ("context",) if "unknown" in actual or not actual else ()
        wrong_assumptions = ("execution_assumption",) if request.reasoning_metadata.get("assumption_risk") else ()
        improvement = ("clarify expectations",) if failure else ("preserve approach",)
        summary = f"Expected '{request.expected_outcome}' and observed '{request.actual_outcome}'."
        self.logger.info("reflection_analyzed reflection_id=%s", request.reflection_id)
        return ReflectionAnalysis(
            summary=summary,
            success_factors=("matched outcome",) if success else (),
            failure_factors=("outcome drift",) if failure else (),
            missing_information=missing_information,
            wrong_assumptions=wrong_assumptions,
            improvement_opportunities=improvement,
        )

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ReflectionAnalyzer must be initialized before use.")
