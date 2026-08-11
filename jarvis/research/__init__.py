"""Local-first research foundation for bounded research planning."""

from .agent import ResearchAgent
from .cli import render_research_command
from .evidence import ResearchEvidenceCollector
from .models import (
    ResearchDepth,
    ResearchEvidence,
    ResearchIntent,
    ResearchPlan,
    ResearchResult,
    ResearchRiskLevel,
    ResearchSourceType,
    ResearchStatus,
    ResearchSummary,
    ResearchQuestion,
)
from .planner import ResearchPlanner, classify_research_intent, classify_research_risk
from .safety import ResearchSafetyDecision, evaluate_research_safety, is_research_allowed, research_source_policy
from .sources import ResearchSourcePolicy, ResearchSourceRequest
from .storage import ResearchHistoryRecord, ResearchHistoryStore
from .runtime import (
    AutonomousResearchRuntime, EvidenceChunk, ExternalResearchPlan,
    ExternalResearchRequest, ExternalResearchResult, KnowledgeCandidate,
    ResearchBudget, ResearchClaim, ResearchSource, SearchProviderRegistry,
    SearchProviderState, SearchResult, SourceType, SupportState, normalize_url,
)

__all__ = [
    "ResearchAgent",
    "ResearchDepth",
    "ResearchEvidence",
    "ResearchEvidenceCollector",
    "ResearchHistoryRecord",
    "ResearchHistoryStore",
    "ResearchIntent",
    "ResearchPlan",
    "ResearchPlanner",
    "ResearchQuestion",
    "ResearchResult",
    "ResearchRiskLevel",
    "ResearchSafetyDecision",
    "ResearchSourcePolicy",
    "ResearchSourceRequest",
    "ResearchSourceType",
    "ResearchStatus",
    "ResearchSummary",
    "AutonomousResearchRuntime", "EvidenceChunk", "ExternalResearchPlan",
    "ExternalResearchRequest", "ExternalResearchResult", "KnowledgeCandidate",
    "ResearchBudget", "ResearchClaim", "ResearchSource", "SearchProviderRegistry",
    "SearchProviderState", "SearchResult", "SourceType", "SupportState", "normalize_url",
    "classify_research_intent",
    "classify_research_risk",
    "evaluate_research_safety",
    "is_research_allowed",
    "render_research_command",
    "research_source_policy",
]
