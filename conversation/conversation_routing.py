"""Deterministic command, conversation, and explicit-goal routing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import re


class ConversationIntent(StrEnum):
    COMMAND = "command"
    GENERAL_CHAT = "general_chat"
    FACTUAL_QA = "factual_qa"
    EXPLANATION = "explanation"
    WRITING = "writing"
    CASUAL = "casual"
    ADVICE = "advice"
    GOAL_CREATE = "goal_create"
    GOAL_UPDATE = "goal_update"
    GOAL_STATUS = "goal_status"
    TASK_CREATE = "task_create"
    WORKFLOW_PLAN = "workflow_plan"
    RESEARCH = "research"
    CODING = "coding"
    BROWSER = "browser"
    DOCUMENT = "document"
    MEMORY = "memory"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ConversationRouteDecision:
    intent: ConversationIntent
    subsystem: str
    confidence: float
    reason: str
    command_matched: bool = False
    goal_routing_allowed: bool = False
    provider_route: str = "none"

    def as_metadata(self) -> dict[str, object]:
        return {
            "intent": self.intent.value,
            "subsystem": self.subsystem,
            "confidence": self.confidence,
            "reason": self.reason,
            "command_matched": self.command_matched,
            "goal_routing_allowed": self.goal_routing_allowed,
            "provider_route": self.provider_route,
        }


_GOAL_CREATE = (
    re.compile(r"\b(?:create|set|add|define|start|track)\s+(?:a\s+|an\s+|my\s+)?(?:short[- ]term\s+|long[- ]term\s+)?goal\b"),
    re.compile(r"\bmake\s+.+\s+(?:my\s+)?goal\b"),
)
_GOAL_UPDATE = (
    re.compile(r"\b(?:update|change|edit|revise|pause|resume|complete|finish|abandon)\s+(?:my\s+|the\s+|this\s+)?(?:[a-z0-9_-]+\s+){0,4}goal\b"),
    re.compile(r"\bmark\s+(?:my\s+|the\s+|this\s+)?goal\s+(?:complete|done|abandoned)\b"),
)
_GOAL_STATUS = (
    re.compile(r"\b(?:show|check|review|list)\s+(?:my\s+|the\s+)?goals?\b"),
    re.compile(r"\b(?:goal|goals)\s+(?:status|progress|portfolio|list)\b"),
)


def _matches(patterns: tuple[re.Pattern[str], ...], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def classify_conversation_route(text: str, *, command_matched: bool = False) -> ConversationRouteDecision:
    """Return an explainable route; uncertainty deliberately falls back to chat."""
    normalized = " ".join(text.strip().lower().split())
    if command_matched:
        return ConversationRouteDecision(
            ConversationIntent.COMMAND, "command_dispatcher", 1.0,
            "Input matched a registered command namespace.", True,
        )
    if _matches(_GOAL_CREATE, normalized):
        return ConversationRouteDecision(ConversationIntent.GOAL_CREATE, "goal_intelligence", 0.96, "Explicit goal creation language was detected.", goal_routing_allowed=True)
    if _matches(_GOAL_UPDATE, normalized):
        return ConversationRouteDecision(ConversationIntent.GOAL_UPDATE, "goal_intelligence", 0.95, "Explicit goal mutation language was detected.", goal_routing_allowed=True)
    if _matches(_GOAL_STATUS, normalized):
        return ConversationRouteDecision(ConversationIntent.GOAL_STATUS, "goal_intelligence", 0.93, "Explicit goal status language was detected.", goal_routing_allowed=True)
    if re.search(r"\b(?:remember|forget)\b", normalized):
        return ConversationRouteDecision(ConversationIntent.MEMORY, "memory_intelligence", 0.86, "Explicit memory intent was detected.")
    if re.search(r"\b(?:research|find sources|literature review)\b", normalized):
        return ConversationRouteDecision(ConversationIntent.RESEARCH, "research_agent", 0.88, "Research language was detected.")
    if re.search(r"\b(?:debug|review (?:this |the )?(?:code|diff|repo)|fix (?:this |the )?(?:bug|code)|refactor)\b", normalized):
        return ConversationRouteDecision(ConversationIntent.CODING, "coding_agent", 0.86, "Coding language was detected.")
    if re.search(r"\b(?:browse|open (?:the )?(?:site|page)|web page)\b", normalized):
        return ConversationRouteDecision(ConversationIntent.BROWSER, "browser_runtime", 0.82, "Browser language was detected.")
    if re.search(r"\b(?:document|pdf|spreadsheet|presentation)\b", normalized):
        return ConversationRouteDecision(ConversationIntent.DOCUMENT, "document_intelligence", 0.8, "Document language was detected.")
    if re.search(r"\b(?:create|add)\s+(?:a\s+)?task\b", normalized):
        return ConversationRouteDecision(ConversationIntent.TASK_CREATE, "task_intelligence", 0.9, "Explicit task creation language was detected.")
    if re.search(r"\b(?:create|run|build)\s+(?:a\s+)?workflow\b", normalized):
        return ConversationRouteDecision(ConversationIntent.WORKFLOW_PLAN, "workflow_runtime", 0.9, "Explicit workflow language was detected.")
    if re.match(r"^(?:explain|teach me|how does|how do|why does|why is)\b", normalized):
        return ConversationRouteDecision(ConversationIntent.EXPLANATION, "conversation_engine", 0.91, "Explanation request detected.", provider_route="local_chat")
    if re.match(r"^(?:write|rewrite|draft|compose)\b", normalized):
        return ConversationRouteDecision(ConversationIntent.WRITING, "conversation_engine", 0.91, "Writing request detected.", provider_route="local_chat")
    if re.search(r"\b(?:joke|who are you|how are you|hello|hi|thanks|thank you)\b", normalized):
        return ConversationRouteDecision(ConversationIntent.CASUAL, "conversation_engine", 0.9, "Casual conversation detected.", provider_route="local_chat")
    if re.match(r"^(?:what should|how can|give me ideas|recommend|advise)\b", normalized):
        return ConversationRouteDecision(ConversationIntent.ADVICE, "conversation_engine", 0.84, "Advice request detected.", provider_route="local_chat")
    if normalized.endswith("?") or re.match(r"^(?:what|who|when|where|which|how many)\b", normalized):
        return ConversationRouteDecision(ConversationIntent.FACTUAL_QA, "conversation_engine", 0.82, "Question form detected.", provider_route="local_chat")
    return ConversationRouteDecision(ConversationIntent.GENERAL_CHAT, "conversation_engine", 0.6, "No explicit specialist intent was detected; safe chat fallback selected.", provider_route="local_chat")


def render_route_decision(decision: ConversationRouteDecision) -> str:
    return (
        f"Route: intent={decision.intent.value} subsystem={decision.subsystem} "
        f"confidence={decision.confidence:.2f} command_matched={'yes' if decision.command_matched else 'no'} "
        f"goal_allowed={'yes' if decision.goal_routing_allowed else 'no'} "
        f"provider={decision.provider_route} reason={decision.reason}"
    )
