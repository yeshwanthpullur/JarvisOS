"""Personal intelligence service built on top of the Memory Engine."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

from memory import Memory, MemoryManager
from personal_intelligence.models import (
    PersonalClassification,
    PersonalInformation,
    PersonalQueryResult,
)
from retrieval import RetrievalContext, RetrievalManager, RetrievalRequest, RetrievalStrategy


_PERSONAL_TAG = "personal-intelligence"
_DEFAULT_LIMIT = 5


@dataclass(frozen=True, slots=True)
class PersonalIntelligenceStatistics:
    """Operational statistics for personal intelligence."""

    personal_intelligence_status: str
    personal_memory_readiness: str
    personal_retrieval_readiness: str
    active_personal_items: int
    explicit_items: int
    inferred_items: int
    confirmed_items: int
    superseded_items: int
    contradictions: int
    retrieval_hits: int
    personalization_applications: int
    personalization_overrides: int
    failures: int
    overall_personal_intelligence_health: str


class PersonalIntelligenceManager:
    """Coordinates personal memory capture, retrieval, and explanation."""

    def __init__(
        self,
        memory_manager: MemoryManager | None = None,
        retrieval_manager: RetrievalManager | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.memory_manager = memory_manager
        self.retrieval_manager = retrieval_manager
        self.logger = logger or logging.getLogger(__name__)
        self.initialized = False
        self.retrieval_hits = 0
        self.personalization_applications = 0
        self.personalization_overrides = 0
        self.failures = 0

    def initialize(self) -> PersonalIntelligenceStatistics:
        self.initialized = True
        self.logger.info("personal_intelligence_initialized")
        return self.statistics()

    def is_ready(self) -> bool:
        return self.initialized and self.memory_manager is not None and self.memory_manager.initialized

    def detect_candidates(
        self,
        text: str,
        source_type: str = "direct_user_statement",
        source_reference: str | None = None,
        conversation_id: str | None = None,
        request_id: str | None = None,
    ) -> tuple[PersonalInformation, ...]:
        normalized = text.strip()
        if not normalized:
            return ()

        candidates: list[tuple[str, str, str, float, str]] = []
        lowered = normalized.lower()
        if match := re.search(r"\bi prefer (?P<value>.+?)(?:[.!?]$|$)", lowered, re.IGNORECASE):
            candidates.append(("communication preference", self._clean_value(match.group("value")), PersonalClassification.EXPLICIT, 0.95, source_type))
        if match := re.search(r"\bi am working on (?P<value>.+?)(?:[.!?]$|$)", lowered, re.IGNORECASE):
            candidates.append(("project reference", self._clean_value(match.group("value")), PersonalClassification.EXPLICIT, 0.9, source_type))
        if match := re.search(r"\bi am a (?P<value>.+?)(?:[.!?]$|$)", lowered, re.IGNORECASE):
            candidates.append(("identity context", self._clean_value(match.group("value")), PersonalClassification.EXPLICIT, 0.85, source_type))
        if match := re.search(r"\bdon'?t recommend (?P<value>.+?) unless necessary(?:[.!?]$|$)", lowered, re.IGNORECASE):
            candidates.append(("provider preference", f"avoid {self._clean_value(match.group('value'))}", PersonalClassification.EXPLICIT, 0.9, source_type))
        if match := re.search(r"\bremember that i prefer (?P<value>.+?)(?:[.!?]$|$)", lowered, re.IGNORECASE):
            candidates.append(("communication preference", self._clean_value(match.group("value")), PersonalClassification.EXPLICIT, 0.95, source_type))

        results: list[PersonalInformation] = []
        for category, value, classification, confidence, evidence_source in candidates:
            result = self.capture(
                category=category,
                value=value,
                source_type=evidence_source,
                source_reference=source_reference or conversation_id or request_id,
                confidence=confidence,
                classification=classification,
                active=True,
                metadata={"conversation_id": conversation_id, "request_id": request_id, "origin": "conversation"},
            )
            if result is not None:
                results.append(result)
        return tuple(results)

    def capture(
        self,
        category: str,
        value: str,
        source_type: str,
        source_reference: str | None,
        confidence: float,
        classification: str,
        *,
        active: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> PersonalInformation | None:
        self._ensure_ready()
        if not self._is_eligible(category, value, confidence, classification):
            self.logger.info("personal_information_ineligible category=%s classification=%s", category, classification)
            return None

        existing = self._find_active_item(category=category, value=value)
        if existing is not None:
            self.personalization_applications += 1
            return existing

        same_category = self._find_active_category_item(category=category)

        item = PersonalInformation(
            item_id=str(uuid4()),
            category=category,
            value=value.strip(),
            source_type=source_type,
            source_reference=source_reference,
            confidence=max(0.0, min(confidence, 1.0)),
            classification=classification,
            created_at=self._now(),
            updated_at=self._now(),
            last_confirmed_at=self._now() if classification == PersonalClassification.EXPLICIT else None,
            active=active,
            superseded=False,
            metadata=metadata or {},
        )
        memory = self.memory_manager.create_memory(
            title=f"Personal {category}",
            content=value.strip(),
            source=source_type,
            importance=max(1, min(int(round(confidence * 5)), 5)),
            tags=(_PERSONAL_TAG, category.replace(" ", "-")),
            project=None,
            session_id=None,
            metadata=self._metadata_for_item(item, metadata or {}),
        )
        stored = self._bind_memory(item, memory.id)
        if same_category is not None:
            self.update(
                same_category.item_id,
                active=False,
                superseded=True,
                superseded_by=stored.item_id,
                contradictions=same_category.contradictions + (stored.item_id,),
                metadata={"superseded_by": stored.item_id},
            )
            self.personalization_overrides += 1
        self.logger.info(
            "personal_information_captured item_id=%s category=%s classification=%s confidence=%s",
            stored.item_id,
            stored.category,
            stored.classification,
            stored.confidence,
        )
        return stored

    def retrieve(
        self,
        query: str,
        *,
        categories: tuple[str, ...] = (),
        active_only: bool = True,
        limit: int = _DEFAULT_LIMIT,
    ) -> PersonalQueryResult:
        self._ensure_ready()
        items = self._relevant_items(query=query, categories=categories, active_only=active_only, limit=limit)
        if items:
            self.retrieval_hits += 1
        return PersonalQueryResult(items=items, confidence=self._average_confidence(items), metadata={"query": query})

    def explain(self, item_id: str) -> dict[str, Any] | None:
        self._ensure_ready()
        record = self._get_item(item_id)
        if record is None:
            return None
        return {
            "item_id": record.item_id,
            "category": record.category,
            "value": record.value,
            "classification": record.classification,
            "confidence": record.confidence,
            "source_type": record.source_type,
            "source_reference": record.source_reference,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "last_confirmed_at": record.last_confirmed_at.isoformat() if record.last_confirmed_at else None,
            "active": record.active,
            "superseded": record.superseded,
            "superseded_by": record.superseded_by,
            "contradictions": record.contradictions,
            "metadata": record.metadata,
        }

    def list_items(self, active_only: bool = True) -> tuple[PersonalInformation, ...]:
        self._ensure_ready()
        return tuple(item for item in self._all_items() if not active_only or item.active)

    def update(
        self,
        item_id: str,
        *,
        value: str | None = None,
        category: str | None = None,
        confidence: float | None = None,
        classification: str | None = None,
        active: bool | None = None,
        superseded: bool | None = None,
        superseded_by: str | None = None,
        contradictions: tuple[str, ...] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PersonalInformation | None:
        self._ensure_ready()
        record = self._get_item(item_id)
        if record is None:
            return None
        updated = PersonalInformation(
            item_id=record.item_id,
            category=category or record.category,
            value=(value or record.value).strip(),
            source_type=record.source_type,
            source_reference=record.source_reference,
            confidence=max(0.0, min(confidence if confidence is not None else record.confidence, 1.0)),
            classification=classification or record.classification,
            created_at=record.created_at,
            updated_at=self._now(),
            last_confirmed_at=self._now() if (classification or record.classification) == PersonalClassification.EXPLICIT else record.last_confirmed_at,
            active=record.active if active is None else active,
            superseded=record.superseded if superseded is None else superseded,
            superseded_by=record.superseded_by if superseded_by is None else superseded_by,
            contradictions=record.contradictions if contradictions is None else contradictions,
            metadata={**record.metadata, **(metadata or {})},
            memory_id=record.memory_id,
        )
        self._persist(updated)
        self.logger.info("personal_information_updated item_id=%s", item_id)
        return updated

    def supersede(self, item_id: str, new_value: str, *, source_type: str, source_reference: str | None, confidence: float, classification: str = PersonalClassification.EXPLICIT) -> PersonalInformation | None:
        self._ensure_ready()
        record = self._get_item(item_id)
        if record is None:
            return None
        successor = self.capture(
            category=record.category,
            value=new_value,
            source_type=source_type,
            source_reference=source_reference,
            confidence=confidence,
            classification=classification,
            metadata={**record.metadata, "supersedes": item_id},
        )
        if successor is None:
            return None
        superseded = PersonalInformation(
            item_id=record.item_id,
            category=record.category,
            value=record.value,
            source_type=record.source_type,
            source_reference=record.source_reference,
            confidence=record.confidence,
            classification=PersonalClassification.SUPERSEDED,
            created_at=record.created_at,
            updated_at=self._now(),
            last_confirmed_at=record.last_confirmed_at,
            active=False,
            superseded=True,
            superseded_by=successor.item_id,
            contradictions=record.contradictions + (successor.item_id,),
            metadata={**record.metadata, "superseded_by": successor.item_id},
            memory_id=record.memory_id,
        )
        self._persist(superseded)
        self.logger.info("personal_information_superseded item_id=%s successor=%s", item_id, successor.item_id)
        return successor

    def confirm(self, item_id: str) -> PersonalInformation | None:
        self._ensure_ready()
        record = self._get_item(item_id)
        if record is None:
            return None
        confirmed = self.update(
            item_id,
            classification=PersonalClassification.EXPLICIT,
            metadata={"confirmed": True},
        )
        if confirmed is not None:
            self.logger.info("personal_information_confirmed item_id=%s", item_id)
        return confirmed

    def reject(self, item_id: str, reason: str = "user rejected") -> PersonalInformation | None:
        self._ensure_ready()
        record = self._get_item(item_id)
        if record is None:
            return None
        rejected = self.update(
            item_id,
            classification=PersonalClassification.DISPUTED,
            active=False,
            superseded=True,
            metadata={"rejected": True, "reason": reason},
        )
        if rejected is not None:
            self.logger.info("personal_information_rejected item_id=%s", item_id)
        return rejected

    def forget(self, item_id: str) -> bool:
        self._ensure_ready()
        record = self._get_item(item_id)
        if record is None or record.memory_id is None:
            return False
        forgotten = self.update(
            item_id,
            classification=PersonalClassification.SUPERSEDED,
            active=False,
            superseded=True,
            metadata={"forgotten": True},
        )
        if forgotten is None:
            return False
        return True

    def apply_context(self, request_text: str, conversation_id: str | None = None) -> dict[str, Any]:
        """Return relevant personal context without over-sharing."""
        personal_items = self.retrieve(request_text).items
        override = self._has_current_override(request_text)
        context = {
            "personal_items": tuple(self._serialize(item) for item in personal_items),
            "active_preferences": tuple(self._serialize(item) for item in personal_items if item.active),
            "override_current_instruction": override,
            "conversation_id": conversation_id,
        }
        if personal_items:
            self.personalization_applications += 1
        return context

    def search(self, query: str, *, limit: int = _DEFAULT_LIMIT) -> tuple[PersonalInformation, ...]:
        """Search through personal memory using existing Retrieval and Memory layers."""
        self._ensure_ready()
        if self.retrieval_manager is not None:
            self.retrieval_manager.context.memory_manager = self.memory_manager
            retrieval = self.retrieval_manager.retrieve(
                RetrievalRequest(
                    intent="personal_context",
                    goal="Retrieve relevant personal context",
                    query=query,
                    required_sources=("memory", "conversation", "workflow", "task"),
                    retrieval_strategy=RetrievalStrategy.HYBRID,
                    context={"personal": True},
                )
            )
            memory_ids = {
                reference.split(":", 1)[-1]
                for reference in retrieval.memory_references
                if reference.startswith("memory:")
            }
            if memory_ids:
                items = tuple(
                    item
                    for item in self._all_items()
                    if item.memory_id in memory_ids and self._matches_query(item, query)
                )
                if items:
                    self.retrieval_hits += 1
                    return items[:limit]
        return self.retrieve(query, limit=limit).items

    def statistics(self) -> PersonalIntelligenceStatistics:
        items = self._all_items()
        active_items = tuple(item for item in items if item.active)
        explicit_items = tuple(item for item in items if item.classification == PersonalClassification.EXPLICIT)
        inferred_items = tuple(item for item in items if item.classification == PersonalClassification.INFERRED)
        confirmed_items = tuple(item for item in items if item.metadata.get("confirmed"))
        superseded_items = tuple(item for item in items if item.superseded)
        contradictions = sum(len(item.contradictions) for item in items)
        return PersonalIntelligenceStatistics(
            personal_intelligence_status="ready" if self.initialized else "unavailable",
            personal_memory_readiness="ready" if self.memory_manager is not None and self.memory_manager.initialized else "unavailable",
            personal_retrieval_readiness="ready" if self.retrieval_manager is not None else "degraded",
            active_personal_items=len(active_items),
            explicit_items=len(explicit_items),
            inferred_items=len(inferred_items),
            confirmed_items=len(confirmed_items),
            superseded_items=len(superseded_items),
            contradictions=contradictions,
            retrieval_hits=self.retrieval_hits,
            personalization_applications=self.personalization_applications,
            personalization_overrides=self.personalization_overrides,
            failures=self.failures,
            overall_personal_intelligence_health="healthy" if self.is_ready() else "degraded",
        )

    def summarize(self, query: str | None = None) -> str:
        items = self.search(query or "personal") if query else self.list_items()
        if not items:
            return "I do not have any durable personal information yet."
        parts = []
        for item in items:
            prefix = "confirmed" if item.classification == PersonalClassification.EXPLICIT else item.classification
            parts.append(f"{item.category}: {item.value} ({prefix}, confidence {item.confidence:.2f})")
        return "; ".join(parts)

    def _bind_memory(self, item: PersonalInformation, memory_id: str) -> PersonalInformation:
        bound = PersonalInformation(
            item_id=item.item_id,
            category=item.category,
            value=item.value,
            source_type=item.source_type,
            source_reference=item.source_reference,
            confidence=item.confidence,
            classification=item.classification,
            created_at=item.created_at,
            updated_at=item.updated_at,
            last_confirmed_at=item.last_confirmed_at,
            active=item.active,
            superseded=item.superseded,
            superseded_by=item.superseded_by,
            contradictions=item.contradictions,
            metadata={**item.metadata, "memory_id": memory_id},
            memory_id=memory_id,
        )
        self._persist(bound)
        return bound

    def _persist(self, item: PersonalInformation) -> None:
        if item.memory_id is None:
            return
        self.memory_manager.update_memory(
            item.memory_id,
            title=f"Personal {item.category}",
            content=item.value,
            source=item.source_type,
            importance=max(1, min(int(round(item.confidence * 5)), 5)),
            tags=(_PERSONAL_TAG, item.category.replace(" ", "-")),
            metadata=self._metadata_for_item(item, item.metadata),
        )

    def _metadata_for_item(self, item: PersonalInformation, metadata: dict[str, Any]) -> dict[str, Any]:
        return {
            **metadata,
            "personal_intelligence": {
                "item_id": item.item_id,
                "category": item.category,
                "value": item.value,
                "source_type": item.source_type,
                "source_reference": item.source_reference,
                "confidence": item.confidence,
                "classification": item.classification,
                "created_at": item.created_at.isoformat(),
                "updated_at": item.updated_at.isoformat(),
                "last_confirmed_at": item.last_confirmed_at.isoformat() if item.last_confirmed_at else None,
                "active": item.active,
                "superseded": item.superseded,
                "superseded_by": item.superseded_by,
                "contradictions": item.contradictions,
                "memory_id": item.memory_id,
            },
        }

    def _get_item(self, item_id: str) -> PersonalInformation | None:
        for item in self._all_items():
            if item.item_id == item_id:
                return item
        return None

    def _find_active_item(self, *, category: str, value: str) -> PersonalInformation | None:
        normalized_category = category.strip().lower()
        normalized_value = self._normalize(value)
        for item in self._all_items():
            if not item.active:
                continue
            if item.category.strip().lower() == normalized_category and self._normalize(item.value) == normalized_value:
                return item
        return None

    def _find_active_category_item(self, *, category: str) -> PersonalInformation | None:
        normalized_category = category.strip().lower()
        for item in self._all_items():
            if item.active and item.category.strip().lower() == normalized_category:
                return item
        return None

    def _all_items(self) -> tuple[PersonalInformation, ...]:
        if self.memory_manager is None:
            return ()
        memories = self.memory_manager.list_memories(limit=1000)
        items = [self._memory_to_personal_information(memory) for memory in memories if self._is_personal_memory(memory)]
        return tuple(sorted(items, key=lambda item: (not item.active, -item.confidence, item.updated_at), reverse=False))

    def _relevant_items(self, query: str, *, categories: tuple[str, ...], active_only: bool, limit: int) -> tuple[PersonalInformation, ...]:
        query_terms = self._normalize(query)
        items = []
        for item in self._all_items():
            if active_only and not item.active:
                continue
            if categories and item.category not in categories:
                continue
            if query_terms and not self._matches_query(item, query):
                continue
            items.append(item)
        items.sort(key=lambda item: (item.confidence, item.active, item.updated_at), reverse=True)
        return tuple(items[:limit])

    def _matches_query(self, item: PersonalInformation, query: str) -> bool:
        terms = self._normalize(query)
        if not terms:
            return True
        haystack = " ".join([item.category, item.value, item.source_type, item.classification, repr(item.metadata)]).lower()
        return any(term in haystack for term in terms.split())

    def _memory_to_personal_information(self, memory: Memory) -> PersonalInformation:
        personal = dict(memory.metadata.get("personal_intelligence", {}))
        return PersonalInformation(
            item_id=str(personal.get("item_id") or memory.id),
            category=str(personal.get("category") or "custom preference"),
            value=str(personal.get("value") or memory.content),
            source_type=str(personal.get("source_type") or memory.source),
            source_reference=personal.get("source_reference"),
            confidence=float(personal.get("confidence") or 0.5),
            classification=str(personal.get("classification") or PersonalClassification.DERIVED),
            created_at=self._parse_datetime(personal.get("created_at"), memory.created_at),
            updated_at=self._parse_datetime(personal.get("updated_at"), memory.updated_at),
            last_confirmed_at=self._parse_datetime(personal.get("last_confirmed_at"), None),
            active=bool(personal.get("active", True)),
            superseded=bool(personal.get("superseded", False)),
            superseded_by=personal.get("superseded_by"),
            contradictions=tuple(personal.get("contradictions", ())),
            metadata={k: v for k, v in memory.metadata.items() if k != "personal_intelligence"},
            memory_id=memory.id,
        )

    def _is_personal_memory(self, memory: Memory) -> bool:
        metadata = memory.metadata.get("personal_intelligence")
        return bool(metadata) or _PERSONAL_TAG in memory.tags

    def _serialize(self, item: PersonalInformation) -> dict[str, Any]:
        return {
            "item_id": item.item_id,
            "category": item.category,
            "value": item.value,
            "source_type": item.source_type,
            "source_reference": item.source_reference,
            "confidence": item.confidence,
            "classification": item.classification,
            "active": item.active,
            "superseded": item.superseded,
            "superseded_by": item.superseded_by,
            "updated_at": item.updated_at.isoformat(),
            "last_confirmed_at": item.last_confirmed_at.isoformat() if item.last_confirmed_at else None,
            "memory_id": item.memory_id,
            "metadata": item.metadata,
        }

    def _is_eligible(self, category: str, value: str, confidence: float, classification: str) -> bool:
        if not category.strip() or not value.strip():
            return False
        if confidence < 0.35 and classification != PersonalClassification.EXPLICIT:
            return False
        return True

    def _clean_value(self, value: str) -> str:
        return value.strip().rstrip(".,;:!?")

    def _normalize(self, value: str) -> str:
        return re.sub(r"\s+", " ", value.strip().lower())

    def _parse_datetime(self, value: Any, fallback: datetime | None) -> datetime | None:
        if isinstance(value, str) and value:
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return fallback
        return fallback

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def _has_current_override(self, request_text: str) -> bool:
        lowered = request_text.lower()
        return any(
            phrase in lowered
            for phrase in (
                "in complete detail",
                "complete detail",
                "be detailed",
                "detailed answer",
                "answer in detail",
                "thoroughly",
            )
        )

    def _average_confidence(self, items: tuple[PersonalInformation, ...]) -> float:
        if not items:
            return 0.0
        return sum(item.confidence for item in items) / len(items)

    def _ensure_ready(self) -> None:
        if not self.initialized:
            raise RuntimeError("PersonalIntelligenceManager must be initialized before use.")
        if self.memory_manager is None or not self.memory_manager.initialized:
            raise RuntimeError("PersonalIntelligenceManager requires an initialized MemoryManager.")
