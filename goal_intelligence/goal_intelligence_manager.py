"""Goal Intelligence orchestration for JARVIS OS."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Any

from task_intelligence import TaskIntelligenceManager
from task_intelligence.models import GoalRecord, MilestoneRecord, TaskPriorityLevel
from tasks import TaskManager, TaskStatus


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class GoalReference:
    """Resolved goal reference."""

    goal_id: str
    title: str
    source: str
    confidence: float
    status: str


@dataclass(frozen=True, slots=True)
class GoalResolution:
    """Resolved goal result."""

    goal: GoalRecord | None
    status: str
    confidence: float
    immediate_response: str


@dataclass(frozen=True, slots=True)
class GoalClarification:
    """Clarification request for a vague goal."""

    goal_text: str
    missing_information: tuple[str, ...]
    questions: tuple[str, ...]
    confidence: float
    reason: str
    immediate_response: str


@dataclass(frozen=True, slots=True)
class GoalQualityReport:
    """Goal quality assessment."""

    goal: GoalRecord
    quality: str
    confidence: float
    findings: tuple[str, ...]
    assumptions: tuple[str, ...]
    missing_information: tuple[str, ...]
    recommendations: tuple[str, ...]
    immediate_response: str


@dataclass(frozen=True, slots=True)
class GoalDecompositionPlan:
    """Goal decomposition into milestones and supporting work."""

    goal: GoalRecord
    milestones: tuple[MilestoneRecord, ...]
    supporting_tasks: tuple[str, ...]
    dependencies: tuple[str, ...]
    first_step: str
    confidence: float
    recommendations: tuple[str, ...]
    immediate_response: str


@dataclass(frozen=True, slots=True)
class GoalProgressReport:
    """Progress evaluation for a goal."""

    goal: GoalRecord
    status: str
    confidence: float
    progress_summary: str
    evidence: tuple[str, ...]
    remaining_work: tuple[str, ...]
    blockers: tuple[str, ...]
    risk: str
    immediate_response: str


@dataclass(frozen=True, slots=True)
class GoalConflictReport:
    """Conflict analysis for a goal portfolio."""

    goals: tuple[GoalRecord, ...]
    conflict_type: str
    affected_goal_ids: tuple[str, ...]
    evidence: tuple[str, ...]
    severity: str
    options: tuple[str, ...]
    confidence: float
    immediate_response: str


@dataclass(frozen=True, slots=True)
class GoalPortfolioEntry:
    """Selective goal portfolio summary entry."""

    goal_id: str
    title: str
    status: str
    priority: str
    progress: float
    deadline_health: str
    main_blocker: str
    next_review: str | None
    next_step: str


@dataclass(frozen=True, slots=True)
class GoalPortfolioReport:
    """Selective goal portfolio summary."""

    entries: tuple[GoalPortfolioEntry, ...]
    confidence: float
    immediate_response: str


@dataclass(frozen=True, slots=True)
class GoalRecommendation:
    """Grounded next-step recommendation."""

    goal: GoalRecord
    reason: str
    confidence: float
    supporting_milestone: str | None = None
    supporting_task: str | None = None
    dependencies: tuple[str, ...] = ()
    blockers: tuple[str, ...] = ()
    alternative_options: tuple[str, ...] = ()
    immediate_response: str = ""


@dataclass(frozen=True, slots=True)
class GoalAnalysisReport:
    """Generic advisory report returned by goal intelligence operations."""

    analysis_type: str
    goal: GoalRecord | None
    confidence: float
    summary: str
    findings: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    evidence: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    immediate_response: str = ""


@dataclass(frozen=True, slots=True)
class GoalIntelligenceStatistics:
    """Operational statistics for Goal Intelligence."""

    goal_intelligence_status: str
    goal_analysis_readiness: str
    goal_decomposition_readiness: str
    goal_progress_readiness: str
    goal_reference_resolution_readiness: str
    active_goals: int
    paused_goals: int
    blocked_goals: int
    goals_at_risk: int
    goal_reviews: int
    successful_decompositions: int
    unaligned_tasks: int
    detected_conflicts: int
    completion_assessments: int
    missing_goal_references: int
    failed_goal_transitions: int
    overall_goal_intelligence_health: str


class GoalIntelligenceManager:
    """Practical goal analysis, decomposition, and review layer."""

    def __init__(
        self,
        *,
        task_intelligence_manager: TaskIntelligenceManager | None = None,
        task_manager: TaskManager | None = None,
        context_intelligence_manager: object | None = None,
        retrieval_manager: object | None = None,
        personal_intelligence_manager: object | None = None,
        workflow_manager: object | None = None,
        research_manager: object | None = None,
        memory_manager: object | None = None,
        knowledge_manager: object | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.task_intelligence_manager = task_intelligence_manager
        self.task_manager = task_manager
        self.context_intelligence_manager = context_intelligence_manager
        self.retrieval_manager = retrieval_manager
        self.personal_intelligence_manager = personal_intelligence_manager
        self.workflow_manager = workflow_manager
        self.research_manager = research_manager
        self.memory_manager = memory_manager
        self.knowledge_manager = knowledge_manager
        self.logger = logger or logging.getLogger(__name__)
        self.initialized = False
        self.goal_reviews = 0
        self.successful_decompositions = 0
        self.unaligned_tasks = 0
        self.detected_conflicts = 0
        self.completion_assessments = 0
        self.missing_goal_references = 0
        self.failed_goal_transitions = 0

    def initialize(self) -> GoalIntelligenceStatistics:
        self.initialized = True
        self.logger.info("goal_intelligence_initialized")
        return self.statistics()

    def clarify_goal(self, goal_text: str, session: object | None = None) -> GoalClarification:
        goal = goal_text.strip()
        missing: list[str] = []
        questions: list[str] = []
        if not self._has_specific_outcome(goal):
            missing.append("desired outcome")
            questions.append("What outcome should this goal produce?")
        if not self._has_success_criteria(goal):
            missing.append("success criteria")
            questions.append("How will we know this goal is done?")
        if not self._has_time_horizon(goal):
            missing.append("time horizon")
            questions.append("Is this a short-term, medium-term, or long-term goal?")
        if not questions:
            questions.append("Do you want me to break this goal into milestones and tasks?")
        response = " ".join(questions)
        self.logger.info("goal_clarified missing=%s", ",".join(missing) or "none")
        return GoalClarification(
            goal_text=goal,
            missing_information=tuple(missing),
            questions=tuple(questions),
            confidence=0.72 if missing else 0.93,
            reason="Selectively surfaced only the information needed to make the goal actionable.",
            immediate_response=response,
        )

    def evaluate_goal_quality(self, goal: GoalRecord) -> GoalQualityReport:
        findings: list[str] = []
        recommendations: list[str] = []
        missing: list[str] = []
        quality = "strong"
        if not goal.desired_outcome and not goal.purpose:
            missing.append("desired outcome")
            findings.append("The goal does not yet describe a clear outcome.")
            quality = "needs_clarification"
        if not goal.success_criteria:
            missing.append("success criteria")
            findings.append("Success criteria are missing.")
            if quality == "strong":
                quality = "usable"
        if goal.target_date is None and goal.time_horizon == "open_ended":
            missing.append("time horizon")
            findings.append("No time horizon or target date is set.")
        if goal.priority == TaskPriorityLevel.DEFERRED:
            findings.append("The goal is intentionally deferred.")
        if goal.status in {"blocked", "at_risk"}:
            quality = "blocked" if goal.status == "blocked" else "at_risk"
        if not recommendations and missing:
            recommendations.append("Add measurable success criteria and a realistic time horizon.")
        if not recommendations:
            recommendations.append("The goal is actionable as written.")
        summary = f"Goal quality is {quality.replace('_', ' ')}."
        self.logger.info("goal_quality_evaluated goal_id=%s quality=%s", goal.goal_id, quality)
        return GoalQualityReport(
            goal=goal,
            quality=quality,
            confidence=0.9 if quality == "strong" else 0.76,
            findings=tuple(findings),
            assumptions=(),
            missing_information=tuple(dict.fromkeys(missing)),
            recommendations=tuple(recommendations),
            immediate_response=f"{summary} {' '.join(findings or recommendations)}".strip(),
        )

    def decompose_goal(self, goal: GoalRecord) -> GoalDecompositionPlan:
        milestones: list[MilestoneRecord] = []
        if self.task_intelligence_manager is not None:
            stage_names = self._milestone_candidates(goal)
            for name in stage_names[:4]:
                milestone = self.task_intelligence_manager.milestone_manager.create_milestone(
                    name,
                    description=f"Milestone for {goal.name}",
                    project_id=goal.project_id,
                    goal_id=goal.goal_id,
                )
                milestones.append(milestone)
                self.task_intelligence_manager.goal_manager.link_milestone(goal.goal_id, milestone.milestone_id)
        supporting_tasks = self._task_candidates(goal)
        if self.task_manager is not None:
            for task_name in supporting_tasks[:3]:
                task = self.task_manager.create_task(
                    task_name,
                    f"Support the goal: {goal.name}",
                    metadata={"goal_id": goal.goal_id},
                )
                self.task_intelligence_manager.goal_manager.link_task(goal.goal_id, task.task_id) if self.task_intelligence_manager else None
        self.successful_decompositions += 1
        first_step = supporting_tasks[0] if supporting_tasks else f"define the first milestone for {goal.name}"
        response = f"First meaningful step: {first_step}."
        self.logger.info("goal_decomposed goal_id=%s milestones=%s", goal.goal_id, len(milestones))
        return GoalDecompositionPlan(
            goal=goal,
            milestones=tuple(milestones),
            supporting_tasks=tuple(supporting_tasks),
            dependencies=goal.dependencies,
            first_step=first_step,
            confidence=0.84,
            recommendations=("Keep the decomposition proportional to the goal complexity.",),
            immediate_response=response,
        )

    def evaluate_progress(self, goal: GoalRecord) -> GoalProgressReport:
        evidence: list[str] = []
        blockers: list[str] = []
        remaining: list[str] = []
        milestone_progress = 0.0
        milestone_count = 0
        task_progress = 0.0
        task_count = 0
        linked_milestones = self._linked_milestones(goal)
        if linked_milestones:
            milestone_count = len(linked_milestones)
            milestone_progress = sum(m.progress for m in linked_milestones) / milestone_count
            evidence.append(f"{sum(1 for item in linked_milestones if item.progress >= 1.0)} milestone(s) completed.")
            for milestone in linked_milestones:
                if milestone.progress < 1.0:
                    remaining.append(f"Finish milestone: {milestone.name}")
        linked_tasks = self._linked_tasks(goal)
        if linked_tasks:
            task_count = len(linked_tasks)
            completed = sum(1 for task in linked_tasks if task.status is TaskStatus.COMPLETED)
            task_progress = completed / task_count
            evidence.append(f"{completed} linked task(s) completed.")
            for task in linked_tasks:
                if task.status in {TaskStatus.FAILED, TaskStatus.PAUSED}:
                    blockers.append(f"Task blocked or failed: {task.name}")
                elif task.status is not TaskStatus.COMPLETED:
                    remaining.append(f"Complete task: {task.name}")
        progress_estimate = round((goal.progress + milestone_progress + task_progress) / max(1, 1 + bool(linked_milestones) + bool(linked_tasks)), 2)
        if progress_estimate >= 1.0 and goal.status == "completed":
            status = "completed"
        elif blockers:
            status = "blocked"
        elif progress_estimate > 0.0 and (task_progress > 0.0 or milestone_progress > 0.0):
            status = "in_progress"
        elif progress_estimate >= 0.75:
            status = "on_track"
        elif progress_estimate >= 0.4:
            status = "in_progress"
        else:
            status = "early"
        risk = goal.risk or ("delivery risk" if blockers else "low")
        if not evidence:
            evidence.append("No authoritative completion evidence was available.")
        self.logger.info("goal_progress_evaluated goal_id=%s status=%s", goal.goal_id, status)
        return GoalProgressReport(
            goal=self._snapshot_goal(goal),
            status=status,
            confidence=0.8 if evidence else 0.55,
            progress_summary=f"Estimated progress: {int(progress_estimate * 100)}% based on authoritative goal, milestone, and task evidence.",
            evidence=tuple(evidence),
            remaining_work=tuple(dict.fromkeys(remaining)) or ("Define the next meaningful step.",),
            blockers=tuple(dict.fromkeys(blockers)),
            risk=risk,
            immediate_response=f"Progress is {status}. {evidence[0]}",
        )

    def detect_blockers(self, goal: GoalRecord) -> tuple[str, ...]:
        blockers: list[str] = list(goal.blocker_references)
        if goal.status == "blocked":
            blockers.append("Goal is already marked blocked in authoritative state.")
        for task in self._linked_tasks(goal):
            if task.status in {TaskStatus.FAILED, TaskStatus.PAUSED}:
                blockers.append(f"Task blocker: {task.name}")
        for dependency in goal.dependencies:
            if not self._goal_exists(dependency):
                blockers.append(f"Missing dependency: {dependency}")
        return tuple(dict.fromkeys(blockers))

    def detect_conflicts(self, goals: tuple[GoalRecord, ...]) -> GoalConflictReport:
        if len(goals) < 2:
            return GoalConflictReport(
                goals=goals,
                conflict_type="insufficient_information",
                affected_goal_ids=tuple(goal.goal_id for goal in goals),
                evidence=("At least two goals are required for conflict comparison.",),
                severity="low",
                options=("Provide another goal for comparison.",),
                confidence=0.4,
                immediate_response="I need at least two goals to compare for conflicts.",
            )
        conflicts: list[str] = []
        if len({goal.target_date for goal in goals if goal.target_date}) < len([goal for goal in goals if goal.target_date]):
            conflicts.append("competing deadlines")
        if any(goal.status == "blocked" for goal in goals) and any(goal.priority == TaskPriorityLevel.CRITICAL for goal in goals):
            conflicts.append("resource contention")
        conflict_type = "confirmed_conflict" if conflicts else "no_conflict"
        severity = "high" if conflicts else "low"
        options = ("Reprioritize one goal.", "Adjust deadlines.", "Reduce scope.", "Sequence the goals.")
        return GoalConflictReport(
            goals=goals,
            conflict_type=conflict_type,
            affected_goal_ids=tuple(goal.goal_id for goal in goals),
            evidence=tuple(conflicts or ("No direct conflict evidence was found.",)),
            severity=severity,
            options=options,
            confidence=0.82 if conflicts else 0.6,
            immediate_response="Conflict detected." if conflicts else "No direct conflict was detected.",
        )

    def recommend_priority(self, goals: tuple[GoalRecord, ...]) -> tuple[GoalRecord, ...]:
        ordered = tuple(
            sorted(
                goals,
                key=lambda goal: (
                    self._priority_score(goal.priority),
                    self._deadline_score(goal.target_date),
                    goal.progress,
                    -self._risk_score(goal.risk),
                ),
                reverse=True,
            )
        )
        self.logger.info("goal_priority_recommended count=%s", len(ordered))
        return ordered

    def compare_goals(self, goals: tuple[GoalRecord, ...]) -> GoalConflictReport:
        ordered = self.recommend_priority(goals)
        evidence = tuple(f"{goal.name}: {goal.priority.value}, progress={goal.progress}" for goal in ordered)
        return GoalConflictReport(
            goals=ordered,
            conflict_type="comparison",
            affected_goal_ids=tuple(goal.goal_id for goal in ordered),
            evidence=evidence,
            severity="informational",
            options=tuple(goal.name for goal in ordered),
            confidence=0.8,
            immediate_response="Goal comparison prepared.",
        )

    def review_goal(self, goal: GoalRecord) -> GoalAnalysisReport:
        self.goal_reviews += 1
        quality = self.evaluate_goal_quality(goal)
        progress = self.evaluate_progress(goal)
        blockers = self.detect_blockers(goal)
        summary = f"{goal.name}: {quality.quality}, {progress.status}, blockers={len(blockers)}."
        self.logger.info("goal_reviewed goal_id=%s", goal.goal_id)
        return GoalAnalysisReport(
            analysis_type="review",
            goal=self._snapshot_goal(goal),
            confidence=min(quality.confidence, progress.confidence),
            summary=summary,
            findings=quality.findings + progress.evidence,
            recommendations=quality.recommendations + progress.remaining_work,
            evidence=progress.evidence,
            metadata={"blockers": blockers, "risk": progress.risk},
            immediate_response=summary,
        )

    def revise_goal(self, goal_id: str, **changes: object) -> GoalAnalysisReport:
        goal = self._goal(goal_id)
        if goal is None:
            self.missing_goal_references += 1
            return GoalAnalysisReport(
                analysis_type="revise",
                goal=None,
                confidence=0.0,
                summary="Goal not found.",
                immediate_response="I could not find that goal.",
            )
        updated = self.task_intelligence_manager.goal_manager.update_goal(goal_id, **changes) if self.task_intelligence_manager else None
        if updated is None:
            self.failed_goal_transitions += 1
        return GoalAnalysisReport(
            analysis_type="revise",
            goal=self._snapshot_goal(goal),
                confidence=0.5,
                summary="Revision failed.",
                immediate_response="I could not update the goal through Task Intelligence.",
            )
        return GoalAnalysisReport(
            analysis_type="revise",
            goal=updated,
            confidence=0.9,
            summary="Goal revised.",
            recommendations=("Review downstream milestones and tasks for alignment.",),
            immediate_response=f"Goal '{updated.name}' was revised.",
        )

    def pause_goal(self, goal_id: str) -> GoalAnalysisReport:
        goal = self._mutate_goal(goal_id, "paused", "paused")
        return goal

    def resume_goal(self, goal_id: str) -> GoalAnalysisReport:
        goal = self._mutate_goal(goal_id, "active", "resumed")
        return goal

    def abandon_goal(self, goal_id: str, reason: str = "") -> GoalAnalysisReport:
        goal = self._goal(goal_id)
        if goal is None:
            self.missing_goal_references += 1
            return GoalAnalysisReport("abandon", None, 0.0, "Goal not found.", immediate_response="I could not find that goal.")
        updated = self.task_intelligence_manager.goal_manager.abandon_goal(goal_id, reason=reason) if self.task_intelligence_manager else None
        if updated is None:
            self.failed_goal_transitions += 1
            return GoalAnalysisReport("abandon", self._snapshot_goal(goal), 0.5, "Abandonment failed.", immediate_response="I could not abandon the goal.")
        return GoalAnalysisReport("abandon", self._snapshot_goal(updated), 0.9, "Goal abandoned.", immediate_response=f"Goal '{updated.name}' was abandoned.")

    def supersede_goal(self, goal_id: str, successor_goal_id: str, reason: str = "") -> GoalAnalysisReport:
        goal = self._goal(goal_id)
        if goal is None:
            self.missing_goal_references += 1
            return GoalAnalysisReport("supersede", None, 0.0, "Goal not found.", immediate_response="I could not find that goal.")
        updated = self.task_intelligence_manager.goal_manager.supersede_goal(goal_id, successor_goal_id, reason=reason) if self.task_intelligence_manager else None
        if updated is None:
            self.failed_goal_transitions += 1
            return GoalAnalysisReport("supersede", self._snapshot_goal(goal), 0.5, "Supersession failed.", immediate_response="I could not supersede the goal.")
        return GoalAnalysisReport("supersede", self._snapshot_goal(updated), 0.9, "Goal superseded.", immediate_response=f"Goal '{updated.name}' was superseded.")

    def evaluate_completion(self, goal: GoalRecord) -> GoalAnalysisReport:
        self.completion_assessments += 1
        progress = self.evaluate_progress(goal)
        if goal.status == "completed" and goal.success_criteria:
            outcome = "completed"
            summary = f"Goal '{goal.name}' is complete."
        elif goal.success_criteria and progress.status == "completed":
            outcome = "likely_completed"
            summary = f"Goal '{goal.name}' appears complete but needs confirmation."
        elif not goal.success_criteria:
            outcome = "insufficient_evidence"
            summary = "Success criteria are missing, so completion cannot be verified."
        else:
            outcome = "not_completed"
            summary = f"Goal '{goal.name}' is not complete yet."
        return GoalAnalysisReport(
            analysis_type="completion",
            goal=self._snapshot_goal(goal),
            confidence=progress.confidence,
            summary=summary,
            findings=(progress.progress_summary,),
            recommendations=( "Confirm completion only after success criteria are satisfied.",),
            evidence=progress.evidence,
            metadata={"outcome": outcome, "remaining_work": progress.remaining_work},
            immediate_response=summary,
        )

    def recommend_next_step(self, goal: GoalRecord) -> GoalRecommendation:
        progress = self.evaluate_progress(goal)
        if progress.blockers:
            reason = f"Resolve the blocker first: {progress.blockers[0]}"
        elif progress.remaining_work:
            reason = progress.remaining_work[0]
        else:
            reason = f"Continue the active goal: {goal.name}"
        supporting_milestone = goal.milestones[0] if goal.milestones else None
        supporting_task = goal.task_references[0] if goal.task_references else None
        return GoalRecommendation(
            goal=goal,
            reason=reason,
            confidence=progress.confidence,
            supporting_milestone=supporting_milestone,
            supporting_task=supporting_task,
            dependencies=goal.dependencies,
            blockers=progress.blockers,
            alternative_options=tuple(progress.remaining_work[1:3]),
            immediate_response=f"Recommended next step: {reason}",
        )

    def goal_portfolio(self) -> GoalPortfolioReport:
        goals = self._all_goals()
        entries = []
        for goal in goals:
            progress = self.evaluate_progress(goal)
            deadline_health = "overdue" if goal.target_date and self._deadline_score(goal.target_date) < 0 else "on_track"
            next_step = self.recommend_next_step(goal).reason
            entries.append(
                GoalPortfolioEntry(
                    goal_id=goal.goal_id,
                    title=goal.name,
                    status=goal.status,
                    priority=goal.priority.value,
                    progress=goal.progress,
                    deadline_health=deadline_health,
                    main_blocker=progress.blockers[0] if progress.blockers else "",
                    next_review=goal.next_review.isoformat() if goal.next_review else None,
                    next_step=next_step,
                )
            )
        priority = tuple(sorted(entries, key=lambda item: (item.deadline_health, item.progress)))
        summary = ", ".join(f"{entry.title}:{entry.status}" for entry in priority[:5]) or "No active goals."
        return GoalPortfolioReport(entries=priority, confidence=0.82, immediate_response=summary)

    def explain_goal_state(self, goal: GoalRecord) -> GoalAnalysisReport:
        progress = self.evaluate_progress(goal)
        blockers = self.detect_blockers(goal)
        summary = f"Goal '{goal.name}' is {goal.status}. {progress.progress_summary}"
        if blockers:
            summary += f" Blockers: {', '.join(blockers)}."
        return GoalAnalysisReport(
            analysis_type="explain",
            goal=goal,
            confidence=progress.confidence,
            summary=summary,
            findings=progress.evidence,
            recommendations=progress.remaining_work,
            evidence=progress.evidence,
            metadata={"blockers": blockers},
            immediate_response=summary,
        )

    def prepare_request(self, goal_text: str, session: object | None = None) -> GoalAnalysisReport:
        """Entry point used by conversation and executive layers."""
        goal = self._resolve_goal(goal_text, session=session)
        normalized = self._normalize(goal_text)
        if goal is None:
            clarification = self.clarify_goal(goal_text, session=session)
            return GoalAnalysisReport(
                analysis_type="clarify",
                goal=None,
                confidence=clarification.confidence,
                summary=clarification.reason,
                findings=clarification.questions,
                recommendations=clarification.questions,
                metadata={"missing_information": clarification.missing_information},
                immediate_response=clarification.immediate_response,
            )
        if self._is_decomposition_request(normalized):
            return self._wrap_decomposition(self.decompose_goal(goal))
        if self._is_progress_request(normalized):
            progress = self.evaluate_progress(goal)
            return GoalAnalysisReport(
                analysis_type="progress",
                goal=goal,
                confidence=progress.confidence,
                summary=progress.progress_summary,
                findings=progress.evidence,
                recommendations=progress.remaining_work,
                evidence=progress.evidence,
                metadata={"blockers": progress.blockers, "risk": progress.risk},
                immediate_response=progress.immediate_response,
            )
        if self._is_next_step_request(normalized):
            recommendation = self.recommend_next_step(goal)
            return GoalAnalysisReport(
                analysis_type="next_step",
                goal=goal,
                confidence=recommendation.confidence,
                summary=recommendation.reason,
                recommendations=(recommendation.reason,),
                metadata={"supporting_milestone": recommendation.supporting_milestone, "supporting_task": recommendation.supporting_task},
                immediate_response=recommendation.immediate_response,
            )
        if self._is_review_request(normalized):
            report = self.review_goal(goal)
            return report
        if self._is_conflict_request(normalized):
            conflicts = self.detect_conflicts(tuple(self._all_goals()))
            return GoalAnalysisReport(
                analysis_type="conflict",
                goal=goal,
                confidence=conflicts.confidence,
                summary=conflicts.immediate_response,
                findings=conflicts.evidence,
                recommendations=conflicts.options,
                metadata={"affected_goal_ids": conflicts.affected_goal_ids, "severity": conflicts.severity},
                immediate_response=conflicts.immediate_response,
            )
        if self._is_portfolio_request(normalized):
            portfolio = self.goal_portfolio()
            return GoalAnalysisReport(
                analysis_type="portfolio",
                goal=goal,
                confidence=portfolio.confidence,
                summary=portfolio.immediate_response,
                findings=tuple(entry.title for entry in portfolio.entries),
                recommendations=tuple(entry.next_step for entry in portfolio.entries[:3]),
                metadata={"entries": portfolio.entries},
                immediate_response=portfolio.immediate_response,
            )
        if self._is_completion_request(normalized):
            return self.evaluate_completion(goal)
        if self._is_pause_request(normalized):
            return self._wrap_mutation(self.pause_goal(goal.goal_id), "pause")
        if self._is_resume_request(normalized):
            return self._wrap_mutation(self.resume_goal(goal.goal_id), "resume")
        if self._is_abandon_request(normalized):
            return self.abandon_goal(goal.goal_id)
        if self._is_revise_request(normalized):
            return self.revise_goal(goal.goal_id)
        return self.explain_goal_state(goal)

    def resolve_goal_reference(self, text: str, session: object | None = None) -> GoalResolution:
        goal = self._resolve_goal(text, session=session)
        if goal is None:
            return GoalResolution(
                goal=None,
                status="missing",
                confidence=0.0,
                immediate_response="I could not find a matching goal.",
            )
        return GoalResolution(
            goal=goal,
            status="resolved",
            confidence=self._goal_confidence(goal),
            immediate_response=f"Resolved goal: {goal.name}",
        )

    def statistics(self) -> GoalIntelligenceStatistics:
        goals = self._all_goals()
        return GoalIntelligenceStatistics(
            goal_intelligence_status="ready" if self.initialized else "unavailable",
            goal_analysis_readiness="ready" if self.initialized else "unavailable",
            goal_decomposition_readiness="ready" if self.initialized else "unavailable",
            goal_progress_readiness="ready" if self.initialized else "unavailable",
            goal_reference_resolution_readiness="ready" if self.initialized else "unavailable",
            active_goals=sum(1 for goal in goals if goal.status == "active"),
            paused_goals=sum(1 for goal in goals if goal.status == "paused"),
            blocked_goals=sum(1 for goal in goals if goal.status == "blocked"),
            goals_at_risk=sum(1 for goal in goals if goal.status == "at_risk"),
            goal_reviews=self.goal_reviews,
            successful_decompositions=self.successful_decompositions,
            unaligned_tasks=self.unaligned_tasks,
            detected_conflicts=self.detected_conflicts,
            completion_assessments=self.completion_assessments,
            missing_goal_references=self.missing_goal_references,
            failed_goal_transitions=self.failed_goal_transitions,
            overall_goal_intelligence_health="healthy" if self.initialized else "degraded",
        )

    def _wrap_decomposition(self, plan: GoalDecompositionPlan) -> GoalAnalysisReport:
        return GoalAnalysisReport(
            analysis_type="decompose",
            goal=plan.goal,
            confidence=plan.confidence,
            summary=plan.immediate_response,
            findings=tuple(milestone.name for milestone in plan.milestones),
            recommendations=plan.recommendations,
            metadata={"first_step": plan.first_step, "supporting_tasks": plan.supporting_tasks},
            immediate_response=plan.immediate_response,
        )

    def _wrap_mutation(self, report: GoalAnalysisReport, action: str) -> GoalAnalysisReport:
        return GoalAnalysisReport(
            analysis_type=action,
            goal=report.goal,
            confidence=report.confidence,
            summary=report.summary,
            findings=report.findings,
            recommendations=report.recommendations,
            evidence=report.evidence,
            metadata=report.metadata,
            immediate_response=report.immediate_response,
        )

    def _mutate_goal(self, goal_id: str, status: str, action: str) -> GoalAnalysisReport:
        goal = self._goal(goal_id)
        if goal is None:
            self.missing_goal_references += 1
            return GoalAnalysisReport(action, None, 0.0, "Goal not found.", immediate_response="I could not find that goal.")
        updated = self.task_intelligence_manager.goal_manager.set_status(goal_id, status) if self.task_intelligence_manager else None
        if updated is None:
            self.failed_goal_transitions += 1
            return GoalAnalysisReport(action, self._snapshot_goal(goal), 0.5, f"Could not set goal to {status}.", immediate_response=f"I could not mark the goal as {status}.")
        return GoalAnalysisReport(action, self._snapshot_goal(updated), 0.9, f"Goal marked {status}.", immediate_response=f"Goal '{updated.name}' is now {status}.")

    def _resolve_goal(self, text: str, session: object | None = None) -> GoalRecord | None:
        normalized = self._normalize(text)
        if session is not None:
            current_goal = getattr(session, "current_goal", None)
            if isinstance(current_goal, str) and current_goal.strip():
                resolved = self._search_goals(current_goal)
                if resolved:
                    return resolved[0]
        if self.context_intelligence_manager is not None and session is not None:
            current = getattr(self.context_intelligence_manager, "current_objective", lambda _: None)(session)
            if current:
                goals = self._search_goals(current)
                if goals:
                    return goals[0]
        goals = self._search_goals(normalized or text)
        if goals:
            return goals[0]
        if self._looks_like_goal_id(normalized):
            goal = self._goal(normalized)
            if goal is not None:
                return goal
        return None

    def _search_goals(self, query: str) -> tuple[GoalRecord, ...]:
        if self.task_intelligence_manager is None:
            return ()
        return self.task_intelligence_manager.goal_manager.search_goals(query)

    def _goal(self, goal_id: str) -> GoalRecord | None:
        if self.task_intelligence_manager is None:
            return None
        return self.task_intelligence_manager.goal_manager.get_goal(goal_id)

    def _all_goals(self) -> tuple[GoalRecord, ...]:
        if self.task_intelligence_manager is None:
            return ()
        return self.task_intelligence_manager.goal_manager.list_goals()

    def _linked_tasks(self, goal: GoalRecord) -> tuple[Any, ...]:
        tasks: list[Any] = []
        if self.task_manager is None:
            return ()
        for task_id in goal.task_references:
            task = self.task_manager.get_task(task_id)
            if task is not None:
                tasks.append(task)
        return tuple(tasks)

    def _linked_milestones(self, goal: GoalRecord) -> tuple[MilestoneRecord, ...]:
        if self.task_intelligence_manager is None:
            return ()
        milestones: list[MilestoneRecord] = []
        for milestone_id in goal.milestones:
            milestone = self.task_intelligence_manager.milestone_manager.get_milestone(milestone_id)
            if milestone is not None:
                milestones.append(milestone)
        return tuple(milestones)

    def _goal_exists(self, goal_id: str) -> bool:
        return self._goal(goal_id) is not None

    def _goal_confidence(self, goal: GoalRecord) -> float:
        confidence = goal.confidence
        if goal.success_criteria:
            confidence += 0.1
        if goal.target_date:
            confidence += 0.05
        return min(confidence, 0.99)

    def _snapshot_goal(self, goal: GoalRecord) -> GoalRecord:
        return replace(goal)

    def _priority_score(self, priority: TaskPriorityLevel) -> int:
        return {
            TaskPriorityLevel.CRITICAL: 5,
            TaskPriorityLevel.HIGH: 4,
            TaskPriorityLevel.NORMAL: 3,
            TaskPriorityLevel.LOW: 2,
            TaskPriorityLevel.DEFERRED: 1,
        }[priority]

    def _deadline_score(self, target_date: str | None) -> int:
        if not target_date:
            return 0
        try:
            parsed = datetime.fromisoformat(target_date)
        except ValueError:
            return 0
        delta = parsed - utc_now()
        return int(-delta.total_seconds())

    def _risk_score(self, risk: str) -> int:
        return 3 if risk and risk != "low" else 1

    def _has_specific_outcome(self, text: str) -> bool:
        return bool(re.search(r"\b(build|create|deliver|ship|launch|improve|complete|design)\b", text, re.I))

    def _has_success_criteria(self, text: str) -> bool:
        return any(marker in text.lower() for marker in ("done", "when", "success", "criteria", "measure", "verify"))

    def _has_time_horizon(self, text: str) -> bool:
        return any(marker in text.lower() for marker in ("today", "this week", "month", "quarter", "year", "short", "medium", "long"))

    def _milestone_candidates(self, goal: GoalRecord) -> tuple[str, ...]:
        base = goal.desired_outcome or goal.name
        return (
            f"Clarify the scope of {base}",
            f"Build the first usable version of {base}",
            f"Validate the result for {base}",
            f"Complete the release criteria for {base}",
        )

    def _task_candidates(self, goal: GoalRecord) -> tuple[str, ...]:
        base = goal.desired_outcome or goal.name
        return (
            f"Define the first step for {base}",
            f"Collect dependencies for {base}",
            f"Implement the next milestone for {base}",
        )

    def _is_decomposition_request(self, normalized: str) -> bool:
        return any(marker in normalized for marker in ("break this goal", "decompose", "milestone", "plan this goal"))

    def _is_progress_request(self, normalized: str) -> bool:
        return any(marker in normalized for marker in ("progress", "making progress", "where are we", "am i making progress"))

    def _is_next_step_request(self, normalized: str) -> bool:
        return any(marker in normalized for marker in ("what should i do next", "next meaningful step", "next step", "what should i do first"))

    def _is_review_request(self, normalized: str) -> bool:
        return "review" in normalized or "evaluate" in normalized or "assess" in normalized

    def _is_conflict_request(self, normalized: str) -> bool:
        return "conflict" in normalized

    def _is_portfolio_request(self, normalized: str) -> bool:
        return any(marker in normalized for marker in ("what goals", "portfolio", "which goals", "goal list", "need attention"))

    def _is_completion_request(self, normalized: str) -> bool:
        return "complete" in normalized or "completion" in normalized

    def _is_pause_request(self, normalized: str) -> bool:
        return "pause" in normalized and "goal" in normalized

    def _is_resume_request(self, normalized: str) -> bool:
        return "resume" in normalized and "goal" in normalized

    def _is_abandon_request(self, normalized: str) -> bool:
        return any(marker in normalized for marker in ("abandon", "no longer relevant", "drop this goal", "supersede"))

    def _is_revise_request(self, normalized: str) -> bool:
        return any(marker in normalized for marker in ("revise", "update the plan", "change the deadline", "change the goal"))

    def _looks_like_goal_id(self, normalized: str) -> bool:
        return bool(re.fullmatch(r"[0-9a-f-]{8,}", normalized))

    def _normalize(self, text: str) -> str:
        normalized = text.strip().lower()
        normalized = re.sub(r"[?!.,;:]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("GoalIntelligenceManager must be initialized before use.")
