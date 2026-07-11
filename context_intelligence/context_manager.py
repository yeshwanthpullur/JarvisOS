"""Practical context tracking and reference resolution for JARVIS OS."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from context_intelligence.models import ContextItem, ContextResolution, utc_now

if TYPE_CHECKING:
    from conversation.conversation_response import ConversationResponse
    from conversation.conversation_session import ConversationSession


_MAX_RECENT_CONTEXTS = 12
_CONTEXT_EXPIRATION = timedelta(hours=12)


@dataclass(frozen=True, slots=True)
class ContextIntelligenceStatistics:
    """Operational readiness and usage statistics."""

    context_intelligence_status: str
    conversation_context_readiness: str
    context_retrieval_readiness: str
    reference_resolution_readiness: str
    continuation_readiness: str
    active_context_count: int
    context_switches: int
    successful_resolutions: int
    ambiguous_resolutions: int
    missing_context: int
    clarifications: int
    successful_continuations: int
    failed_continuations: int
    stale_references: int
    overall_context_intelligence_health: str


class ContextIntelligenceManager:
    """Tracks active context and resolves continuity-dependent requests."""

    def __init__(
        self,
        *,
        retrieval_manager: object | None = None,
        personal_intelligence_manager: object | None = None,
        task_manager: object | None = None,
        task_intelligence_manager: object | None = None,
        workflow_manager: object | None = None,
        research_manager: object | None = None,
        memory_manager: object | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.retrieval_manager = retrieval_manager
        self.personal_intelligence_manager = personal_intelligence_manager
        self.task_manager = task_manager
        self.task_intelligence_manager = task_intelligence_manager
        self.workflow_manager = workflow_manager
        self.research_manager = research_manager
        self.memory_manager = memory_manager
        self.logger = logger or logging.getLogger(__name__)
        self.initialized = False
        self.context_switches = 0
        self.successful_resolutions = 0
        self.ambiguous_resolutions = 0
        self.missing_context = 0
        self.clarifications = 0
        self.successful_continuations = 0
        self.failed_continuations = 0
        self.stale_references = 0

    def initialize(self) -> ContextIntelligenceStatistics:
        """Initialize the context intelligence service."""
        self.initialized = True
        self.logger.info("context_intelligence_initialized")
        return self.statistics()

    def prepare_request(self, text: str, session: ConversationSession) -> ContextResolution:
        """Resolve context-dependent input and update active session state."""
        self._ensure_initialized()
        normalized = self._normalize(text)
        self._expire_stale_context(session)

        if self._is_clear_request(normalized):
            self.clear_active_context(session)
            resolution = ContextResolution(
                request_type="clear_context",
                status="cleared",
                confidence=1.0,
                active_objective=None,
                immediate_response="I cleared the active context. Your projects, tasks, memory, and history are still intact.",
            )
            self.logger.info("context_cleared conversation_id=%s", session.conversation_id)
            return resolution

        if self._is_pause_request(normalized):
            suspended = self.suspend_current_context(session)
            if suspended is None:
                self.missing_context += 1
                return ContextResolution(
                    request_type="pause_context",
                    status="missing",
                    reason="No active context is available to pause.",
                    immediate_response="There is no active context to pause right now.",
                )
            return ContextResolution(
                request_type="pause_context",
                status="suspended",
                confidence=1.0,
                resolved_item=suspended,
                active_objective=self.current_objective(session),
                immediate_response=f"I paused the current {suspended.context_type}: {suspended.value}.",
            )

        if self._is_resume_request(normalized) and not self._is_continuation_request(normalized):
            return self.resume_previous_context(session)

        if self._is_previous_request(normalized):
            return self.resume_previous_context(session)

        if self._is_status_request(normalized):
            return self.describe_current_context(session)

        explicit_candidates = self.resolve_reference(text, session, explicit_only=True)
        if explicit_candidates.status == "resolved":
            self._activate_item(session, explicit_candidates.resolved_item)
            self._set_objective(session, self._objective_from_request(text, explicit_candidates.resolved_item))
            self.logger.info(
                "context_activated conversation_id=%s type=%s value=%s",
                session.conversation_id,
                explicit_candidates.resolved_item.context_type,
                explicit_candidates.resolved_item.value,
            )
            return explicit_candidates
        if explicit_candidates.ambiguity:
            return explicit_candidates

        if self._is_continuation_request(normalized):
            return self.determine_continuation(session)

        if self._is_meaningful_request(normalized):
            self._set_objective(session, text.strip())
            self._set_last_action(session, text.strip())
        return ContextResolution(
            request_type="request",
            status="none",
            confidence=0.0,
            active_objective=self.current_objective(session),
        )

    def record_interaction(
        self,
        session: ConversationSession,
        request_text: str,
        response: ConversationResponse,
    ) -> None:
        """Capture minimal continuation metadata from a completed interaction."""
        self._ensure_initialized()
        state = self._state(session)
        if request_text.strip():
            state["last_user_request"] = request_text.strip()
        if response.response.strip():
            state["last_result"] = response.response.strip()
        execution_summary = dict(response.execution_summary)
        if execution_summary:
            state["last_execution_summary"] = execution_summary
            next_step = self._derive_next_step(execution_summary)
            if next_step:
                state["pending_state"] = {
                    "kind": "planned_next_step",
                    "message": next_step,
                    "source": "execution_summary",
                }
        if response.warnings:
            state["pending_state"] = {
                "kind": "pending_clarification",
                "message": response.warnings[0],
                "source": "response_warning",
            }
            state["unresolved_question"] = response.warnings[0]
        session.updated_at = utc_now()

    def resolve_reference(
        self,
        text: str,
        session: ConversationSession,
        *,
        explicit_only: bool = False,
    ) -> ContextResolution:
        """Resolve explicit or referential context expressions."""
        self._ensure_initialized()
        candidates = self._collect_candidates(text, session, explicit_only=explicit_only)
        if not candidates:
            return ContextResolution(request_type="reference", status="missing", reason="No compatible context candidates were found.")

        if len(candidates) == 1:
            item = candidates[0]
            if self._is_stale(item):
                self.stale_references += 1
                self.logger.info("stale_reference_detected type=%s value=%s", item.context_type, item.value)
                return ContextResolution(
                    request_type="reference",
                    status="stale",
                    confidence=item.confidence,
                    resolved_item=item,
                    reason="The referenced context no longer maps to an available authoritative record.",
                    stale_reference=True,
                )
            self.successful_resolutions += 1
            self.logger.info("reference_resolved type=%s value=%s", item.context_type, item.value)
            return ContextResolution(
                request_type="reference",
                status="resolved",
                confidence=item.confidence,
                resolved_item=item,
                active_objective=self.current_objective(session),
            )

        ranked = tuple(sorted(candidates, key=lambda item: (item.priority, item.confidence, item.last_active_time), reverse=True))
        top = ranked[0]
        if len(ranked) > 1 and abs(top.confidence - ranked[1].confidence) <= 0.1:
            self.ambiguous_resolutions += 1
            self.clarifications += 1
            labels = ", ".join(item.value for item in ranked[:3])
            self.logger.info("reference_ambiguous candidates=%s", labels)
            return ContextResolution(
                request_type="reference",
                status="ambiguous",
                confidence=top.confidence,
                candidates=ranked[:3],
                reason="Multiple plausible context candidates remain active.",
                suggested_clarification=f"Do you mean {labels}?",
                ambiguity=True,
                immediate_response=f"I found more than one plausible match. Do you mean {labels}?",
            )

        if self._is_stale(top):
            self.stale_references += 1
            return ContextResolution(
                request_type="reference",
                status="stale",
                confidence=top.confidence,
                resolved_item=top,
                reason="The strongest context candidate is stale.",
                stale_reference=True,
            )

        self.successful_resolutions += 1
        return ContextResolution(
            request_type="reference",
            status="resolved",
            confidence=top.confidence,
            resolved_item=top,
            candidates=ranked[:3],
            active_objective=self.current_objective(session),
        )

    def determine_continuation(self, session: ConversationSession) -> ContextResolution:
        """Determine the grounded next continuation for the current session."""
        self._ensure_initialized()
        state = self._state(session)
        pending = dict(state.get("pending_state") or {})
        if pending:
            if pending.get("kind") == "stale_reference":
                self.failed_continuations += 1
                return ContextResolution(
                    request_type="continuation",
                    status="stale",
                    confidence=0.9,
                    resolved_item=None,
                    active_objective=self.current_objective(session),
                    pending_state=pending,
                    next_step=pending.get("message"),
                    stale_reference=True,
                    immediate_response=str(pending.get("message") or "The active context is stale."),
                )
            self.successful_continuations += 1
            return ContextResolution(
                request_type="continuation",
                status="resolved",
                confidence=0.95,
                resolved_item=self.current_context(session),
                active_objective=self.current_objective(session),
                pending_state=pending,
                next_step=pending.get("message"),
                immediate_response=f"We stopped on a pending item: {pending.get('message', 'additional input is needed')}.",
            )

        current = self.current_context(session)
        if current is None:
            self.failed_continuations += 1
            self.missing_context += 1
            return ContextResolution(
                request_type="continuation",
                status="missing",
                reason="No active or resumable context is available.",
                immediate_response="I do not have a reliable continuation context right now.",
            )

        if self._is_stale(current):
            self.failed_continuations += 1
            self.stale_references += 1
            return ContextResolution(
                request_type="continuation",
                status="stale",
                confidence=current.confidence,
                resolved_item=current,
                reason="The active context points to a stale or unavailable record.",
                stale_reference=True,
                immediate_response=f"The active {current.context_type} is no longer available, so I cannot continue it safely.",
            )

        next_step = self._next_step_for_item(current, session)
        self.successful_continuations += 1
        return ContextResolution(
            request_type="continuation",
            status="resolved",
            confidence=current.confidence,
            resolved_item=current,
            active_objective=self.current_objective(session),
            next_step=next_step,
            immediate_response=f"We were working on {current.value}. Next grounded step: {next_step}.",
        )

    def describe_current_context(self, session: ConversationSession) -> ContextResolution:
        """Describe the active objective, work item, and pending state."""
        current = self.current_context(session)
        objective = self.current_objective(session)
        pending = self.pending_state(session)
        if current is None and not objective and not pending:
            self.missing_context += 1
            return ContextResolution(
                request_type="status",
                status="missing",
                immediate_response="There is no active context right now.",
            )
        parts: list[str] = []
        if objective:
            parts.append(f"Current objective: {objective}.")
        if current is not None:
            parts.append(f"Active {current.context_type}: {current.value}.")
        if pending:
            parts.append(f"Pending state: {pending.get('message', 'pending work exists')}.")
        return ContextResolution(
            request_type="status",
            status="resolved",
            confidence=current.confidence if current else 0.9,
            resolved_item=current,
            active_objective=objective,
            pending_state=pending,
            immediate_response=" ".join(parts),
        )

    def resume_previous_context(self, session: ConversationSession) -> ContextResolution:
        """Restore the most recent suspended or previous valid context."""
        previous = self.previous_context(session)
        if previous is None:
            self.missing_context += 1
            return ContextResolution(
                request_type="resume_previous",
                status="missing",
                immediate_response="I could not find a previous context to resume.",
            )
        if self._is_stale(previous):
            self.stale_references += 1
            return ContextResolution(
                request_type="resume_previous",
                status="stale",
                resolved_item=previous,
                stale_reference=True,
                immediate_response=f"The previous {previous.context_type} is no longer available.",
            )
        self._activate_item(session, previous)
        self.successful_resolutions += 1
        return ContextResolution(
            request_type="resume_previous",
            status="resolved",
            confidence=previous.confidence,
            resolved_item=previous,
            active_objective=self.current_objective(session),
            immediate_response=f"I restored the previous {previous.context_type}: {previous.value}.",
        )

    def clear_active_context(self, session: ConversationSession) -> bool:
        """Deactivate the current active context without touching authoritative records."""
        state = self._state(session)
        current = self.current_context(session)
        if current is not None:
            self._push_history(session, self._item_to_dict(self._touch(current, active=False)))
        state["current"] = None
        state["objective"] = None
        state["pending_state"] = None
        state["unresolved_question"] = None
        state["active_by_type"] = {}
        session.current_topic = None
        session.current_goal = None
        session.current_workflow = None
        return True

    def suspend_current_context(self, session: ConversationSession) -> ContextItem | None:
        """Suspend the current active context while preserving it in recent history."""
        current = self.current_context(session)
        if current is None:
            return None
        suspended = self._touch(current, active=False)
        self._push_history(session, self._item_to_dict(suspended))
        state = self._state(session)
        state["current"] = None
        state["pending_state"] = {
            "kind": "suspended_context",
            "message": f"Resume {current.value}",
            "source": "context_suspend",
        }
        self.context_switches += 1
        self.logger.info("context_suspended type=%s value=%s", current.context_type, current.value)
        return suspended

    def current_context(self, session: ConversationSession) -> ContextItem | None:
        """Return the current active context item."""
        payload = self._state(session).get("current")
        if not payload:
            return None
        return self._dict_to_item(payload)

    def previous_context(self, session: ConversationSession) -> ContextItem | None:
        """Return the most recent previous context."""
        history = self._recent_items(session)
        return history[0] if history else None

    def list_recent_context(self, session: ConversationSession) -> tuple[ContextItem, ...]:
        """Return bounded recent context history."""
        return self._recent_items(session)

    def current_objective(self, session: ConversationSession) -> str | None:
        """Return the current objective string, if any."""
        return self._state(session).get("objective")

    def pending_state(self, session: ConversationSession) -> dict[str, Any]:
        """Return pending or unresolved continuation state."""
        return dict(self._state(session).get("pending_state") or {})

    def set_pending_state(self, session: ConversationSession, kind: str, message: str) -> None:
        """Public helper for tests and runtime integrations."""
        self._state(session)["pending_state"] = {"kind": kind, "message": message, "source": "manual"}
        self.logger.info("pending_state_set kind=%s", kind)

    def statistics(self) -> ContextIntelligenceStatistics:
        """Return readiness and usage statistics."""
        return ContextIntelligenceStatistics(
            context_intelligence_status="ready" if self.initialized else "unavailable",
            conversation_context_readiness="ready" if self.initialized else "unavailable",
            context_retrieval_readiness="ready" if self.retrieval_manager is not None else "degraded",
            reference_resolution_readiness="ready" if self.initialized else "unavailable",
            continuation_readiness="ready" if self.initialized else "unavailable",
            active_context_count=0,
            context_switches=self.context_switches,
            successful_resolutions=self.successful_resolutions,
            ambiguous_resolutions=self.ambiguous_resolutions,
            missing_context=self.missing_context,
            clarifications=self.clarifications,
            successful_continuations=self.successful_continuations,
            failed_continuations=self.failed_continuations,
            stale_references=self.stale_references,
            overall_context_intelligence_health="healthy" if self.initialized else "degraded",
        )

    def _collect_candidates(
        self,
        text: str,
        session: ConversationSession,
        *,
        explicit_only: bool,
    ) -> tuple[ContextItem, ...]:
        normalized = self._normalize(text)
        candidates: list[ContextItem] = []

        explicit_projects = self._match_projects(normalized)
        for project in explicit_projects:
            candidates.append(
                self._context_item(
                    context_type="project_reference",
                    value=project["name"],
                    source="task_intelligence",
                    source_reference=project["id"],
                    confidence=project["confidence"],
                    priority=400,
                )
            )

        explicit_workflows = self._match_workflows(normalized)
        for workflow in explicit_workflows:
            candidates.append(
                self._context_item(
                    context_type="workflow_reference",
                    value=workflow["name"],
                    source="workflow",
                    source_reference=workflow["id"],
                    confidence=workflow["confidence"],
                    priority=350,
                )
            )

        if "research" in normalized:
            recent_research = self._latest_research()
            if recent_research is not None:
                candidates.append(
                    self._context_item(
                        context_type="research_reference",
                        value=recent_research["topic"],
                        source="research",
                        source_reference=recent_research["id"],
                        confidence=0.75,
                        priority=250,
                    )
                )

        if not explicit_only:
            current = self.current_context(session)
            if current is not None and self._matches_reference(current, normalized):
                candidates.append(self._touch(current, confidence=max(current.confidence, 0.9), priority=current.priority + 50))
            for item in self._recent_items(session):
                if self._matches_reference(item, normalized):
                    candidates.append(item)

        unique: dict[tuple[str, str, str | None], ContextItem] = {}
        for candidate in candidates:
            key = (candidate.context_type, candidate.value, candidate.source_reference)
            previous = unique.get(key)
            if previous is None or candidate.confidence > previous.confidence:
                unique[key] = candidate
        return tuple(unique.values())

    def _match_projects(self, normalized: str) -> tuple[dict[str, Any], ...]:
        manager = getattr(self.task_intelligence_manager, "project_manager", None)
        if manager is None or not getattr(manager, "initialized", False):
            return ()
        matches: list[dict[str, Any]] = []
        for project in manager.list_projects():
            name = self._normalize(project.name)
            if name and name in normalized:
                matches.append({"id": project.project_id, "name": project.name, "confidence": 0.98})
            elif "project" in normalized and self._normalize(project.name.split()[0]) in normalized:
                matches.append({"id": project.project_id, "name": project.name, "confidence": 0.78})
        return tuple(matches)

    def _match_workflows(self, normalized: str) -> tuple[dict[str, Any], ...]:
        manager = self.workflow_manager
        if manager is None:
            return ()
        matches: list[dict[str, Any]] = []
        for record in manager.registry._records.values():
            name = self._normalize(record.definition.name)
            workflow_id = self._normalize(record.workflow_id)
            if name and name in normalized or workflow_id and workflow_id in normalized:
                matches.append({"id": record.workflow_id, "name": record.definition.name, "confidence": 0.95})
        return tuple(matches)

    def _latest_research(self) -> dict[str, Any] | None:
        history = getattr(self.research_manager, "history", None)
        records = getattr(history, "_records", None)
        if not records:
            return None
        record = records[-1]
        return {"id": record.research_id, "topic": record.topic}

    def _matches_reference(self, item: ContextItem, normalized: str) -> bool:
        if not normalized:
            return False
        if item.context_type.split("_")[0] in normalized:
            return True
        if self._normalize(item.value) in normalized:
            return True
        if any(token in normalized for token in ("this", "that", "it", "current one", "same settings")):
            return item.active
        if "previous" in normalized or "earlier" in normalized:
            return not item.active
        if any(token in normalized for token in ("continue", "resume", "next", "go on")):
            return item.active
        return False

    def _activate_item(self, session: ConversationSession, item: ContextItem | None) -> None:
        if item is None:
            return
        state = self._state(session)
        current = self.current_context(session)
        if current is not None and current.identifier != item.identifier:
            self._push_history(session, self._item_to_dict(self._touch(current, active=False)))
            self.context_switches += 1
            self.logger.info("context_switched from=%s to=%s", current.value, item.value)
        touched = self._touch(item, active=True)
        state["current"] = self._item_to_dict(touched)
        state.setdefault("active_by_type", {})[touched.context_type] = self._item_to_dict(touched)
        session.current_topic = touched.context_type.replace("_", " ")
        if touched.context_type == "project_reference":
            session.metadata["active_project_reference"] = touched.source_reference
        if touched.context_type == "workflow_reference":
            session.current_workflow = touched.source_reference or touched.value
        session.updated_at = utc_now()

    def _set_objective(self, session: ConversationSession, objective: str | None) -> None:
        if objective:
            self._state(session)["objective"] = objective
            session.current_goal = objective

    def _set_last_action(self, session: ConversationSession, action: str) -> None:
        self._state(session)["last_action"] = action

    def _next_step_for_item(self, item: ContextItem, session: ConversationSession) -> str:
        pending = self.pending_state(session)
        if pending.get("message"):
            return str(pending["message"])
        if item.context_type == "project_reference":
            return f"continue the active work for {item.value}"
        if item.context_type == "workflow_reference":
            return f"resume the next pending workflow step for {item.value}"
        if item.context_type == "research_reference":
            return f"continue the next research step for {item.value}"
        return f"continue the active objective for {item.value}"

    def _derive_next_step(self, execution_summary: dict[str, Any]) -> str | None:
        if execution_summary.get("goal"):
            return f"finish the remaining work for {execution_summary['goal']}"
        if execution_summary.get("strategy"):
            return f"continue using the {execution_summary['strategy']} strategy"
        return None

    def _is_stale(self, item: ContextItem) -> bool:
        if item.expires_at is not None and utc_now() > item.expires_at:
            return True
        if item.context_type == "project_reference":
            manager = getattr(self.task_intelligence_manager, "project_manager", None)
            if manager is None or not getattr(manager, "initialized", False):
                return False
            return all(project.project_id != item.source_reference for project in manager.list_projects())
        if item.context_type == "task_reference":
            if self.task_manager is None or not getattr(self.task_manager, "initialized", False):
                return False
            return self.task_manager.get_task(item.source_reference or "") is None
        if item.context_type == "workflow_reference":
            if self.workflow_manager is None:
                return False
            return self.workflow_manager.registry.lookup(item.source_reference or "") is None
        if item.context_type == "research_reference":
            latest = self._latest_research()
            return latest is None or latest["id"] != item.source_reference
        return False

    def _expire_stale_context(self, session: ConversationSession) -> None:
        current = self.current_context(session)
        if current is not None and self._is_stale(current):
            state = self._state(session)
            state["current"] = None
            state["pending_state"] = {
                "kind": "stale_reference",
                "message": f"The previous {current.context_type} is no longer available.",
                "source": "context_expiration",
            }
            self.logger.info("context_expired type=%s value=%s", current.context_type, current.value)

    def _recent_items(self, session: ConversationSession) -> tuple[ContextItem, ...]:
        history = self._state(session).get("recent_contexts", [])
        return tuple(self._dict_to_item(item) for item in history)

    def _push_history(self, session: ConversationSession, item: dict[str, Any]) -> None:
        state = self._state(session)
        history = list(state.get("recent_contexts", []))
        history.insert(0, item)
        state["recent_contexts"] = history[:_MAX_RECENT_CONTEXTS]

    def _context_item(
        self,
        *,
        context_type: str,
        value: str,
        source: str,
        source_reference: str | None,
        confidence: float,
        priority: int,
        scope: str = "conversation",
    ) -> ContextItem:
        now = utc_now()
        return ContextItem(
            context_type=context_type,
            value=value,
            scope=scope,
            source=source,
            source_reference=source_reference,
            confidence=confidence,
            created_time=now,
            updated_time=now,
            last_active_time=now,
            expires_at=now + _CONTEXT_EXPIRATION,
            priority=priority,
        )

    def _state(self, session: ConversationSession) -> dict[str, Any]:
        state = session.current_context
        state.setdefault("current", None)
        state.setdefault("recent_contexts", [])
        state.setdefault("active_by_type", {})
        state.setdefault("objective", None)
        state.setdefault("pending_state", None)
        state.setdefault("unresolved_question", None)
        return state

    def _item_to_dict(self, item: ContextItem) -> dict[str, Any]:
        return {
            "identifier": item.identifier,
            "context_type": item.context_type,
            "value": item.value,
            "scope": item.scope,
            "source": item.source,
            "source_reference": item.source_reference,
            "confidence": item.confidence,
            "created_time": item.created_time.isoformat(),
            "updated_time": item.updated_time.isoformat(),
            "last_active_time": item.last_active_time.isoformat(),
            "expires_at": item.expires_at.isoformat() if item.expires_at else None,
            "active": item.active,
            "priority": item.priority,
            "parent_context": item.parent_context,
            "related_context": item.related_context,
            "resolution_metadata": item.resolution_metadata,
        }

    def _dict_to_item(self, payload: dict[str, Any]) -> ContextItem:
        return ContextItem(
            identifier=str(payload.get("identifier")),
            context_type=str(payload.get("context_type", "objective")),
            value=str(payload.get("value", "")),
            scope=str(payload.get("scope", "conversation")),
            source=str(payload.get("source", "conversation")),
            source_reference=payload.get("source_reference"),
            confidence=float(payload.get("confidence", 0.5)),
            created_time=self._parse_time(payload.get("created_time")),
            updated_time=self._parse_time(payload.get("updated_time")),
            last_active_time=self._parse_time(payload.get("last_active_time")),
            expires_at=self._parse_time(payload.get("expires_at"), allow_none=True),
            active=bool(payload.get("active", True)),
            priority=int(payload.get("priority", 100)),
            parent_context=payload.get("parent_context"),
            related_context=tuple(payload.get("related_context", ()) or ()),
            resolution_metadata=dict(payload.get("resolution_metadata", {}) or {}),
        )

    def _touch(
        self,
        item: ContextItem,
        *,
        active: bool | None = None,
        confidence: float | None = None,
        priority: int | None = None,
    ) -> ContextItem:
        now = utc_now()
        return ContextItem(
            identifier=item.identifier,
            context_type=item.context_type,
            value=item.value,
            scope=item.scope,
            source=item.source,
            source_reference=item.source_reference,
            confidence=item.confidence if confidence is None else confidence,
            created_time=item.created_time,
            updated_time=now,
            last_active_time=now,
            expires_at=now + _CONTEXT_EXPIRATION,
            active=item.active if active is None else active,
            priority=item.priority if priority is None else priority,
            parent_context=item.parent_context,
            related_context=item.related_context,
            resolution_metadata=dict(item.resolution_metadata),
        )

    def _parse_time(self, value: Any, *, allow_none: bool = False):
        if value in {None, ""} and allow_none:
            return None
        if isinstance(value, str):
            try:
                from datetime import datetime

                return datetime.fromisoformat(value)
            except ValueError:
                pass
        return utc_now()

    def _objective_from_request(self, text: str, item: ContextItem | None) -> str:
        if item is not None and item.context_type == "project_reference":
            return f"Continue work on {item.value}"
        if item is not None and item.context_type == "workflow_reference":
            return f"Resume workflow {item.value}"
        return text.strip()

    def _is_status_request(self, normalized: str) -> bool:
        return normalized in {
            "what are we working on",
            "what were we doing",
            "show current context",
            "show active context",
            "current context",
            "current objective",
        }

    def _is_continuation_request(self, normalized: str) -> bool:
        return normalized in {"continue", "next", "resume", "go on"} or normalized.startswith("continue ")

    def _is_previous_request(self, normalized: str) -> bool:
        return "previous" in normalized or normalized.startswith("go back")

    def _is_clear_request(self, normalized: str) -> bool:
        return normalized in {"clear context", "clear the current context", "forget that for now"}

    def _is_pause_request(self, normalized: str) -> bool:
        return normalized in {"pause this", "pause current context"}

    def _is_resume_request(self, normalized: str) -> bool:
        return normalized in {"resume this", "resume previous context"}

    def _is_meaningful_request(self, normalized: str) -> bool:
        if not normalized:
            return False
        if normalized in {"help", "status", "version", "clear", "exit"}:
            return False
        if self._is_status_request(normalized) or self._is_continuation_request(normalized):
            return False
        return len(normalized.split()) >= 3

    def _normalize(self, text: str) -> str:
        normalized = text.strip().lower()
        normalized = re.sub(r"[?!.,;:]+", " ", normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    def _ensure_initialized(self) -> None:
        if not self.initialized:
            raise RuntimeError("ContextIntelligenceManager must be initialized before use.")
