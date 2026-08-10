"""Research safety and source policy helpers."""

from __future__ import annotations

from .models import ResearchIntent, ResearchRiskLevel, ResearchSourceType
from .sources import ResearchSourcePolicy


def is_research_allowed(query: str, intent: ResearchIntent) -> tuple[bool, ResearchRiskLevel, str]:
    lowered = query.lower()
    blocked_terms = ("credential", "doxx", "private person", "stalk", "minors", "weapon", "evade law", "self-harm")
    if any(term in lowered for term in blocked_terms):
        return False, ResearchRiskLevel.BLOCKED, "The request is blocked by research safety policy."
    if intent in {ResearchIntent.MARKET_RESEARCH, ResearchIntent.PRODUCT_RESEARCH, ResearchIntent.TECHNICAL_RESEARCH, ResearchIntent.LITERATURE_REVIEW, ResearchIntent.REPO_RESEARCH, ResearchIntent.DOCUMENT_QUESTION, ResearchIntent.WEB_QUESTION}:
        return True, ResearchRiskLevel.MEDIUM if intent in {ResearchIntent.MARKET_RESEARCH, ResearchIntent.PRODUCT_RESEARCH, ResearchIntent.LITERATURE_REVIEW} else ResearchRiskLevel.LOW, "Research request accepted."
    return True, ResearchRiskLevel.LOW, "Research request accepted."


def research_source_policy(*, web_available: bool = True, documents_available: bool = True) -> ResearchSourcePolicy:
    sources = [ResearchSourceType.PROJECT, ResearchSourceType.USER]
    if documents_available:
        sources.append(ResearchSourceType.DOCUMENT)
    if web_available:
        sources.append(ResearchSourceType.WEB)
    return ResearchSourcePolicy(tuple(sources), tuple(source for source in ResearchSourceType if source not in sources))

