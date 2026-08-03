"""Bounded, local-first conversation state and follow-up resolution."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class ConversationMode(str, Enum):
    NORMAL = "normal"
    TEACHING = "teaching"
    DISCUSSION = "discussion"
    BRAINSTORMING = "brainstorming"
    DEBUGGING = "debugging"
    PROJECT = "project"
    INTERVIEW = "interview"


@dataclass(frozen=True, slots=True)
class ConversationConfig:
    enabled: bool = True
    max_turns: int = 12
    max_topics: int = 6
    summary_threshold: int = 8
    reference_resolution: bool = True
    clarification_enabled: bool = True
    max_context_chars: int = 6000


@dataclass(slots=True)
class ConversationTurn:
    user: str
    assistant: str = ""
    topic: str | None = None
    intent: str = "normal"


@dataclass(slots=True)
class ConversationIntelligenceState:
    active_topic: str | None = None
    previous_topic: str | None = None
    recent_entities: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    pending_clarification: str | None = None
    active_comparison: tuple[str, str] | None = None
    confidence: float = 1.0
    unresolved_references: list[str] = field(default_factory=list)
    user_intent: str = "normal"
    mode: ConversationMode = ConversationMode.NORMAL
    turns: list[ConversationTurn] = field(default_factory=list)
    summary: str = ""


@dataclass(frozen=True, slots=True)
class ConversationPlan:
    original_input: str
    provider_input: str
    intent: str
    confidence: float
    topic: str | None
    clarification: str | None = None
    interrupted: bool = False


class ConversationIntelligenceManager:
    """Resolve bounded context without persisting transcripts or changing memory."""

    _FOLLOW_UPS = {
        "explain more": "expand", "go deeper": "expand", "simplify": "simplify",
        "make it shorter": "shorten", "give examples": "examples", "compare": "compare",
        "summarize": "summarize", "repeat": "repeat", "explain again": "repeat",
        "continue": "continue", "why": "why", "how": "how", "advantages": "advantages",
        "disadvantages": "disadvantages", "applications": "applications",
    }
    _REFERENCES = re.compile(r"\b(it|that|those|them|this|these|former|latter|same one|previous|again|before that|ones?)\b", re.I)
    _STOP_WORDS = frozenset({"the", "tell", "explain", "about", "what", "with", "from", "that", "this", "compare", "make", "give", "more", "again", "shorter", "summarize", "please", "would", "could", "should", "have", "does", "into", "than", "then", "they", "their"})

    def __init__(self, config: ConversationConfig | object | None = None) -> None:
        raw = config or ConversationConfig()
        values = {key: getattr(raw, key) for key in ConversationConfig.__dataclass_fields__ if hasattr(raw, key)}
        self.config = ConversationConfig(**values)
        self.state = ConversationIntelligenceState()

    def prepare(self, user_input: str, extra_context: dict[str, object] | None = None) -> ConversationPlan:
        text = user_input.strip()
        lowered = text.lower().rstrip(".!?")
        if not self.config.enabled:
            return ConversationPlan(text, text, "normal", 1.0, self.state.active_topic)
        interrupted = lowered in {"wait", "stop", "no", "forget that", "different question"} or lowered.startswith("actually")
        if lowered in {"wait", "stop"}:
            self.state.pending_clarification = None
            return ConversationPlan(text, "Acknowledge the interruption briefly and pause the current thread.", "interrupt", 1.0, self.state.active_topic, interrupted=True)
        if lowered in {"forget that", "different question"}:
            self._clear_active_thread()
            return ConversationPlan(text, "Acknowledge that the prior topic was dropped and invite the new question briefly.", "topic_reset", 1.0, None, interrupted=True)

        intent = self._intent(lowered)
        mode = self._detect_mode(lowered)
        if mode is not None:
            self.state.mode = mode
        entities = self._extract_entities(text)
        topic = self.state.active_topic if intent != "normal" else (" ".join(entities[-3:])[:100] if entities else self.state.active_topic)
        references = tuple(match.group(0).lower() for match in self._REFERENCES.finditer(text))
        candidates = self._reference_candidates()
        confidence = 1.0
        clarification = None
        if references and self.config.reference_resolution:
            if not candidates and (intent != "normal" or len(lowered.split()) <= 3):
                confidence, clarification = 0.2, "What does that refer to?"
            elif not candidates:
                confidence = 0.65
            elif intent == "normal" and len(candidates) > 1 and self._ambiguous_reference(lowered):
                confidence, clarification = 0.45, f"Did you mean {candidates[0]} or {candidates[1]}?"
            else:
                confidence = 0.9
        if clarification and self.config.clarification_enabled:
            self.state.pending_clarification = clarification
            self.state.unresolved_references = list(references)
            self.state.confidence = confidence
            return ConversationPlan(text, text, intent, confidence, topic, clarification, interrupted)

        self.state.pending_clarification = None
        self.state.unresolved_references.clear()
        if topic and topic != self.state.active_topic:
            self.state.previous_topic = self.state.active_topic
            self.state.active_topic = topic
            self._append_unique(self.state.topics, topic, self.config.max_topics)
        for entity in entities:
            self._append_unique(self.state.recent_entities, entity, 8)
        comparison = self._comparison(text, candidates, entities)
        if comparison:
            self.state.active_comparison = comparison
        self.state.user_intent = intent
        self.state.confidence = confidence
        provider_input = self._build_provider_input(text, intent, extra_context or {})
        self.state.turns.append(ConversationTurn(text, topic=self.state.active_topic, intent=intent))
        self._bound_turns()
        return ConversationPlan(text, provider_input, intent, confidence, self.state.active_topic, interrupted=interrupted)

    def record_response(self, response: str) -> None:
        if self.state.turns:
            self.state.turns[-1].assistant = response[:2000]
        if len(self.state.turns) >= self.config.summary_threshold:
            self.state.summary = self._make_summary()

    def reset(self) -> None:
        self.state = ConversationIntelligenceState()

    def status_text(self) -> str:
        state = self.state
        return f"Conversation: enabled={'yes' if self.config.enabled else 'no'} mode={state.mode.value} topic={state.active_topic or 'none'} turns={len(state.turns)} confidence={state.confidence:.2f} clarification={'pending' if state.pending_clarification else 'none'}."

    def summary_text(self) -> str:
        return self.state.summary or self._make_summary() or "No conversation context is available yet."

    def topic_text(self) -> str:
        return f"Conversation topic: current={self.state.active_topic or 'none'} previous={self.state.previous_topic or 'none'}."

    def confidence_text(self) -> str:
        return f"Conversation confidence: {self.state.confidence:.2f}."

    def mode_text(self) -> str:
        return f"Conversation mode: {self.state.mode.value}."

    def _build_provider_input(self, text: str, intent: str, extra_context: dict[str, object]) -> str:
        lines = ["[Conversation context - use only when relevant]"]
        if self.state.active_topic: lines.append(f"Active topic: {self.state.active_topic}")
        if self.state.previous_topic: lines.append(f"Previous topic: {self.state.previous_topic}")
        if self.state.recent_entities: lines.append("Recent entities: " + ", ".join(self.state.recent_entities[-6:]))
        if self.state.active_comparison: lines.append("Active comparison: " + " vs ".join(self.state.active_comparison))
        if self.state.summary: lines.append("Bounded summary: " + self.state.summary)
        if intent != "normal": lines.append(f"Follow-up intent: {intent}; apply it to the last relevant answer/topic.")
        for key in ("vision_context", "web_context"):
            value = extra_context.get(key)
            if value: lines.append(f"{key.replace('_', ' ').title()}: {str(value)[:500]}")
        if self.state.turns:
            lines.append("Recent turns:")
            for turn in self.state.turns[-3:]:
                lines.append(f"User: {turn.user[:400]}")
                if turn.assistant: lines.append(f"Assistant: {turn.assistant[:600]}")
        lines.extend(("Do not invent unresolved context. Answer the current request directly.", "Current user request: " + text))
        return "\n".join(lines)[: self.config.max_context_chars]

    def _intent(self, lowered: str) -> str:
        for phrase, intent in self._FOLLOW_UPS.items():
            if lowered == phrase or lowered.startswith(phrase + " "): return intent
        return "correction" if lowered.startswith("actually") else "normal"

    def _detect_mode(self, lowered: str) -> ConversationMode | None:
        markers = {ConversationMode.TEACHING:("teach me","explain","lesson"), ConversationMode.BRAINSTORMING:("brainstorm","ideas for"), ConversationMode.DEBUGGING:("debug","traceback","error"), ConversationMode.PROJECT:("project","build","implement"), ConversationMode.INTERVIEW:("interview me","mock interview"), ConversationMode.DISCUSSION:("discuss","debate")}
        return next((mode for mode, phrases in markers.items() if any(phrase in lowered for phrase in phrases)), None)

    def _extract_entities(self, text: str) -> list[str]:
        words = re.findall(r"[A-Za-z][A-Za-z0-9-]{2,}", text)
        return list(dict.fromkeys(word.lower() for word in words if word.lower() not in self._STOP_WORDS))[-4:]

    def _reference_candidates(self) -> list[str]:
        values = list(self.state.active_comparison or ())
        if not values and self.state.active_topic: values.append(self.state.active_topic)
        return values[:2]

    @staticmethod
    def _ambiguous_reference(lowered: str) -> bool:
        return any(word in lowered.split() for word in ("it", "that", "this", "one")) and "former" not in lowered and "latter" not in lowered

    def _comparison(self, text: str, candidates: list[str], entities: list[str]) -> tuple[str, str] | None:
        if "compare" not in text.lower(): return None
        left = candidates[0] if candidates else self.state.active_topic
        right = " ".join(entities[-2:]) if entities else None
        return (left, right) if left and right and left != right else None

    def _make_summary(self) -> str:
        if not self.state.turns: return ""
        topics = ", ".join(self.state.topics[-self.config.max_topics:]) or "general conversation"
        intents = ", ".join(dict.fromkeys(turn.intent for turn in self.state.turns[-6:]))
        return f"Discussed {topics}; recent intents: {intents}."[:1000]

    def _bound_turns(self) -> None:
        self.state.turns = self.state.turns[-self.config.max_turns:]

    def _clear_active_thread(self) -> None:
        self.state.previous_topic, self.state.active_topic = self.state.active_topic, None
        self.state.active_comparison = None
        self.state.recent_entities.clear()
        self.state.pending_clarification = None

    @staticmethod
    def _append_unique(values: list[str], value: str, limit: int) -> None:
        if value in values: values.remove(value)
        values.append(value)
        del values[:-limit]
