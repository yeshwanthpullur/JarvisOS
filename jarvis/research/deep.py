"""Bounded multi-stage technical research planning and synthesis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import uuid4

from jarvis.workers.assurance import evidence_integrity
from jarvis.workers.assurance_models import EvidenceRecord, EvidenceType
from .runtime import EvidenceChunk, ExternalResearchPlan, ExternalResearchRequest, ResearchClaim, SourceType, SupportState, AutonomousResearchRuntime


class ResearchRole(StrEnum):
    RESEARCH_PLANNER = "research_planner"
    SOURCE_SCOUT = "source_scout"
    TECHNICAL_RESEARCHER = "technical_researcher"
    SOURCE_REVIEWER = "source_reviewer"
    SYNTHESIS_REVIEWER = "synthesis_reviewer"


class FindingKind(StrEnum):
    DIRECT_SOURCE_FINDING = "direct_source_finding"
    INFERENCE = "inference"
    MODEL_INTERPRETATION = "model_interpretation"
    UNRESOLVED = "unresolved"


@dataclass(frozen=True, slots=True)
class DeepResearchTask:
    task_id: str
    question: str
    role: ResearchRole
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ResearchSynthesis:
    synthesis_id: str
    status: str
    findings: tuple[tuple[FindingKind, str, tuple[str, ...]], ...]
    conflicts: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    warnings: tuple[str, ...] = ()


class DeepResearchCoordinator:
    def __init__(self, runtime: AutonomousResearchRuntime, *, max_subtasks: int = 8, max_retries: int = 1) -> None:
        self.runtime = runtime; self.max_subtasks = max(2, min(max_subtasks, 12)); self.max_retries = max(0, min(max_retries, 2))

    def plan(self, request: ExternalResearchRequest) -> tuple[ExternalResearchPlan, tuple[DeepResearchTask, ...]]:
        plan = self.runtime.plan(request)
        tasks = [DeepResearchTask("research-plan", plan.normalized_question, ResearchRole.RESEARCH_PLANNER)]
        for index, question in enumerate(plan.subquestions or (plan.normalized_question,), 1):
            tasks.append(DeepResearchTask(f"source-{index}", question, ResearchRole.SOURCE_SCOUT, ("research-plan",)))
            tasks.append(DeepResearchTask(f"technical-{index}", question, ResearchRole.TECHNICAL_RESEARCHER, (f"source-{index}",)))
        technical = tuple(item.task_id for item in tasks if item.role is ResearchRole.TECHNICAL_RESEARCHER)
        tasks.append(DeepResearchTask("source-review", "Review source quality and contradictions", ResearchRole.SOURCE_REVIEWER, technical))
        tasks.append(DeepResearchTask("synthesis-review", "Verify bounded synthesis", ResearchRole.SYNTHESIS_REVIEWER, ("source-review",)))
        return plan, tuple(tasks[: self.max_subtasks])

    def synthesize(self, claims: tuple[ResearchClaim, ...], evidence: tuple[EvidenceChunk, ...]) -> ResearchSynthesis:
        evidence_ids = {item.evidence_id for item in evidence}
        findings = []
        conflicts = []
        for claim in claims[:12]:
            valid = tuple(ref for ref in claim.evidence_ids if ref in evidence_ids)
            if claim.support_state is SupportState.CONFLICTING or claim.contradiction_ids: conflicts.append(claim.claim_id)
            kind = FindingKind.DIRECT_SOURCE_FINDING if valid and claim.support_state not in {SupportState.UNSUPPORTED, SupportState.UNKNOWN} else FindingKind.UNRESOLVED
            findings.append((kind, claim.statement[:600], valid))
        unsupported = any(kind is FindingKind.UNRESOLVED for kind, _, _ in findings)
        return ResearchSynthesis(f"synthesis-{uuid4().hex[:12]}", "degraded" if unsupported or conflicts else "completed", tuple(findings), tuple(conflicts), tuple(sorted(evidence_ids))[:32], ("Unsupported conclusions remain unresolved.",) if unsupported else ())

    @staticmethod
    def proof_of_work(task_id: str, synthesis: ResearchSynthesis) -> EvidenceRecord:
        summary = f"Research synthesis status={synthesis.status} findings={len(synthesis.findings)} conflicts={len(synthesis.conflicts)}"
        reference = f"research:{synthesis.synthesis_id}"
        return EvidenceRecord(task_id, synthesis.synthesis_id, EvidenceType.RESEARCH_SOURCE, "deep_research", summary, reference, validated=synthesis.status == "completed", integrity=evidence_integrity(summary, reference))
