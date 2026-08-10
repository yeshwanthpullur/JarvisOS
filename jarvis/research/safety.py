"""Research safety and source policy helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .models import ResearchIntent, ResearchRiskLevel, ResearchSourceType
from .sources import ResearchSourcePolicy


@dataclass(frozen=True, slots=True)
class ResearchSafetyDecision:
    allowed: bool
    risk_level: ResearchRiskLevel
    reason: str
    restricted_domain: str | None = None
    action_confirmation_required: bool = False


_BLOCKED_TERMS = (
    "credential theft", "steal credential", "password theft", "doxx", "private personal details",
    "track a real person", "stalk", "sexual content involving minors", "child sexual", "build a weapon",
    "illegal weapon", "evade law enforcement", "bypass a security system", "extremist operational",
    "self-harm instructions", "how to self-harm", "suicide method", "build a bomb", "make malware",
    "write ransomware", "phishing credentials", "disable security controls",
)
_RESTRICTED_DOMAINS = {
    "medical": ("medical", "diagnosis", "medication", "treatment"),
    "legal": ("legal advice", "lawsuit", "criminal charge", "court case"),
    "financial": ("financial advice", "investment", "stock trade", "tax advice"),
    "safety_critical_engineering": ("flight controller", "drone", "robotics", "chemical", "structural safety"),
}
_ACTION_TERMS = ("instructions", "procedure", "steps to", "execute", "deploy", "build", "control", "operate")


def evaluate_research_safety(query: str, intent: ResearchIntent) -> ResearchSafetyDecision:
    lowered = query.lower()
    if any(term in lowered for term in _BLOCKED_TERMS):
        return ResearchSafetyDecision(False, ResearchRiskLevel.BLOCKED, "The request is blocked by research safety policy.")
    domain = next((name for name, terms in _RESTRICTED_DOMAINS.items() if any(term in lowered for term in terms)), None)
    if domain:
        action_required = any(term in lowered for term in _ACTION_TERMS)
        return ResearchSafetyDecision(
            True,
            ResearchRiskLevel.HIGH if action_required else ResearchRiskLevel.MEDIUM,
            "Restricted-domain research is limited to high-level information, uncertainty, and authoritative sources.",
            restricted_domain=domain,
            action_confirmation_required=action_required,
        )
    if intent in {ResearchIntent.MARKET_RESEARCH, ResearchIntent.PRODUCT_RESEARCH, ResearchIntent.TECHNICAL_RESEARCH, ResearchIntent.LITERATURE_REVIEW, ResearchIntent.REPO_RESEARCH, ResearchIntent.DOCUMENT_QUESTION, ResearchIntent.WEB_QUESTION}:
        risk = ResearchRiskLevel.MEDIUM if intent in {ResearchIntent.MARKET_RESEARCH, ResearchIntent.PRODUCT_RESEARCH, ResearchIntent.LITERATURE_REVIEW} else ResearchRiskLevel.LOW
        return ResearchSafetyDecision(True, risk, "Research request accepted.")
    return ResearchSafetyDecision(True, ResearchRiskLevel.LOW, "Research request accepted.")


def is_research_allowed(query: str, intent: ResearchIntent) -> tuple[bool, ResearchRiskLevel, str]:
    decision = evaluate_research_safety(query, intent)
    return decision.allowed, decision.risk_level, decision.reason


def research_source_policy(*, web_available: bool = True, documents_available: bool = True) -> ResearchSourcePolicy:
    sources = [ResearchSourceType.PROJECT, ResearchSourceType.USER]
    if documents_available:
        sources.append(ResearchSourceType.DOCUMENT)
    if web_available:
        sources.append(ResearchSourceType.WEB)
    return ResearchSourcePolicy(tuple(sources), tuple(source for source in ResearchSourceType if source not in sources))
