"""Higher-level persistent memory intelligence for JARVIS OS."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import hashlib
import logging
import re
from pathlib import Path
from typing import Any
from uuid import uuid4

from memory.memory_manager import MemoryManager
from memory.models import (
    Memory,
    MemoryCreate,
    MemoryConsolidationResult,
    MemoryDeletionRequest,
    MemoryQuery,
    MemorySearchResult,
    MemorySensitivity,
    MemorySource,
    MemoryStatistics,
    MemoryStatus,
    MemorySummary,
    MemoryType,
    MemoryUpdate,
    MemoryWriteRequest,
    utc_now,
)


_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password|bearer)\b"),
    re.compile(r"(?i)\b(openai|anthropic|google|azure|aws|github|slack)_[A-Za-z0-9_-]{8,}\b"),
)


@dataclass(frozen=True, slots=True)
class MemoryIntelligenceStatus:
    """Status snapshot for the higher-level memory intelligence layer."""

    enabled: bool
    local_only: bool
    auto_remember: bool
    auto_session_summary: bool
    repository_ready: bool
    secret_detection_enabled: bool
    consolidation_enabled: bool
    total_memories: int
    total_sessions: int
    max_context_items: int
    max_context_chars: int
    audit_enabled: bool
    status: str
    last_error: str | None = None


@dataclass(frozen=True, slots=True)
class MemoryAuditEvent:
    """Bounded audit record for local memory actions."""

    timestamp: datetime
    action: str
    status: str
    item_count: int = 0
    memory_ids: tuple[str, ...] = ()
    summary: str = ""
    error: str | None = None


@dataclass(frozen=True, slots=True)
class MemoryPreferences:
    """Safe memory policy preferences."""

    local_only: bool = True
    auto_remember: bool = False
    auto_session_summary: bool = True
    sensitive_storage_enabled: bool = False
    secret_detection_enabled: bool = True
    consolidation_enabled: bool = True


class MemoryIntelligenceManager:
    """High-level local memory policy, retrieval, and persistence helper."""

    def __init__(
        self,
        memory_manager: MemoryManager,
        *,
        local_only: bool = True,
        auto_remember: bool = False,
        auto_session_summary: bool = True,
        max_records: int = 2000,
        max_search_results: int = 12,
        max_context_items: int = 8,
        max_context_chars: int = 6000,
        audit_enabled: bool = True,
        audit_retention: int = 100,
        default_retention_days: int = 3650,
        sensitive_storage_enabled: bool = False,
        consolidation_enabled: bool = True,
        secret_detection_enabled: bool = True,
        logger: logging.Logger | None = None,
    ) -> None:
        self.memory_manager = memory_manager
        self.local_only = local_only
        self.auto_remember = auto_remember
        self.auto_session_summary = auto_session_summary
        self.max_records = max(1, int(max_records))
        self.max_search_results = max(1, int(max_search_results))
        self.max_context_items = max(1, int(max_context_items))
        self.max_context_chars = max(256, int(max_context_chars))
        self.audit_enabled = audit_enabled
        self.audit_retention = max(0, int(audit_retention))
        self.default_retention_days = max(1, int(default_retention_days))
        self.sensitive_storage_enabled = sensitive_storage_enabled
        self.secret_detection_enabled = secret_detection_enabled
        self.consolidation_enabled = consolidation_enabled
        self._logger = logger or logging.getLogger(__name__)
        self.initialized = False
        self._audit: list[MemoryAuditEvent] = []
        self._last_safe_reply: str | None = None

    def initialize(self) -> MemoryIntelligenceStatus:
        """Initialize memory intelligence."""
        self.memory_manager.initialize() if not self.memory_manager.initialized else None
        self.initialized = True
        self._logger.info("memory_intelligence_initialized")
        return self.status()

    def status(self) -> MemoryIntelligenceStatus:
        """Return a bounded status snapshot."""
        statistics = self.memory_manager.statistics() if self.memory_manager.initialized else MemoryStatistics(
            total_memories=0,
            total_sessions=0,
            database_size_bytes=0,
            database_path=self.memory_manager.database_path,
        )
        return MemoryIntelligenceStatus(
            enabled=self.memory_manager.initialized,
            local_only=self.local_only,
            auto_remember=self.auto_remember,
            auto_session_summary=self.auto_session_summary,
            repository_ready=self.memory_manager.verify_schema(),
            secret_detection_enabled=self.secret_detection_enabled,
            consolidation_enabled=self.consolidation_enabled,
            total_memories=statistics.total_memories,
            total_sessions=statistics.total_sessions,
            max_context_items=self.max_context_items,
            max_context_chars=self.max_context_chars,
            audit_enabled=self.audit_enabled,
            status="ready" if self.initialized else "unavailable",
        )

    def preferences(self) -> MemoryPreferences:
        return MemoryPreferences(
            local_only=self.local_only,
            auto_remember=self.auto_remember,
            auto_session_summary=self.auto_session_summary,
            sensitive_storage_enabled=self.sensitive_storage_enabled,
            secret_detection_enabled=self.secret_detection_enabled,
            consolidation_enabled=self.consolidation_enabled,
        )

    def is_secret_like(self, text: str) -> bool:
        return any(pattern.search(text) for pattern in _SECRET_PATTERNS)

    def should_store(self, text: str, memory_type: str, sensitivity: str, user_confirmed: bool) -> bool:
        if not text.strip():
            return False
        if sensitivity == MemorySensitivity.PROHIBITED:
            return False
        if not self.sensitive_storage_enabled and sensitivity in {MemorySensitivity.SENSITIVE, MemorySensitivity.PROHIBITED}:
            return False
        if self.secret_detection_enabled and self.is_secret_like(text):
            return False
        if memory_type == MemoryType.CONVERSATION_SUMMARY and not user_confirmed and not self.auto_session_summary:
            return False
        return True

    def remember(
        self,
        title: str,
        content: str,
        *,
        memory_type: str = MemoryType.CUSTOM_NOTE,
        sensitivity: str = MemorySensitivity.NORMAL,
        source: str = MemorySource.EXPLICIT_USER,
        importance: int = 1,
        tags: tuple[str, ...] = (),
        project: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        confidence: float = 0.7,
        user_confirmed: bool = False,
    ) -> Memory | None:
        """Persist a memory if policy permits it."""
        if not self.should_store(content, memory_type, sensitivity, user_confirmed):
            self._record_audit("remember", "blocked", 0, summary=title or "memory blocked")
            return None
        if self.memory_manager.count_memories() >= self.max_records:
            self._record_audit("remember", "blocked", 0, summary="memory limit reached")
            return None
        checksum = hashlib.sha256(content.strip().encode("utf-8")).hexdigest()
        created = self.memory_manager.create_memory(
            title=title.strip() or self._summarize_title(content),
            content=content.strip(),
            source=source,
            importance=importance,
            tags=tags,
            project=project,
            session_id=session_id,
            metadata={
                **(metadata or {}),
                "memory_type": memory_type,
                "sensitivity": sensitivity,
                "confidence": confidence,
                "user_confirmed": user_confirmed,
                "checksum": checksum,
                "version": 1,
                "memory_source": source,
                "memory_created_by": "memory_intelligence",
                "expiration_at": (utc_now() + timedelta(days=self.default_retention_days)).isoformat(),
                "normalized_content": content.strip().lower(),
            },
        )
        self._record_audit("remember", "stored", 1, (created.id,), created.title)
        return created

    def auto_remember_turn(
        self,
        user_text: str,
        assistant_text: str,
        *,
        conversation_id: str,
        session_id: str | None = None,
    ) -> Memory | None:
        """Persist a small conversation summary when automatic summaries are enabled."""
        if not self.auto_remember and not self.auto_session_summary:
            return None
        if not assistant_text.strip():
            return None
        summary = self._build_session_summary(user_text, assistant_text)
        return self.remember(
            title=f"Conversation summary {conversation_id}",
            content=summary,
            memory_type=MemoryType.CONVERSATION_SUMMARY,
            sensitivity=MemorySensitivity.PERSONAL,
            source=MemorySource.AUTOMATIC_SESSION,
            importance=1,
            tags=("conversation", "summary"),
            project="JarvisOS",
            session_id=session_id or conversation_id,
            metadata={"conversation_id": conversation_id},
            confidence=0.55,
            user_confirmed=False,
        )

    def search(self, query: str, *, limit: int | None = None) -> tuple[MemorySearchResult, ...]:
        """Rank memories by a light-weight lexical score."""
        if not query.strip():
            return ()
        search_limit = min(self.max_search_results, max(1, limit or self.max_search_results))
        query_tokens = tuple(token for token in self._tokenize(query) if len(token) > 1)
        memories = self.memory_manager.list_memories(limit=self.max_records)
        scored: list[MemorySearchResult] = []
        for memory in memories:
            if memory.status not in {MemoryStatus.ACTIVE, MemoryStatus.ARCHIVED}:
                continue
            if memory.sensitivity == MemorySensitivity.PROHIBITED and not self.sensitive_storage_enabled:
                continue
            score, reasons = self._score_memory(query_tokens, memory)
            if score <= 0:
                continue
            scored.append(MemorySearchResult(memory=memory, relevance=score, reasons=reasons))
        scored.sort(key=lambda item: (-item.relevance, -item.memory.updated_at.timestamp(), item.memory.title.lower()))
        results = tuple(scored[:search_limit])
        self._record_audit("search", "ok", len(results), tuple(item.memory.id for item in results), query[:120])
        return results

    def memory_context(self, query: str, *, limit: int | None = None) -> MemorySummary | None:
        """Build a bounded context summary from the best matching memories."""
        results = self.search(query, limit=limit)
        if not results:
            return None
        selected = results[: self.max_context_items]
        content_parts: list[str] = []
        memory_ids: list[str] = []
        total_chars = 0
        for result in selected:
            snippet = self._bounded_snippet(result.memory.content)
            line = f"{result.memory.title}: {snippet}"
            if total_chars + len(line) > self.max_context_chars:
                break
            content_parts.append(line)
            memory_ids.append(result.memory.id)
            total_chars += len(line)
        if not content_parts:
            return None
        return MemorySummary(
            title=f"Relevant memory for: {self._summarize_title(query)}",
            content="\n".join(content_parts),
            memory_ids=tuple(memory_ids),
            memory_type=MemoryType.CONVERSATION_SUMMARY,
            confidence=max(item.relevance for item in selected),
            tags=tuple(sorted({tag for item in selected for tag in item.memory.tags})),
        )

    def list(self, limit: int = 100, offset: int = 0) -> tuple[Memory, ...]:
        return self.memory_manager.list_memories(limit=limit, offset=offset)

    def get(self, memory_id: str) -> Memory | None:
        return self.memory_manager.get_memory(memory_id)

    def forget(self, memory_id: str) -> bool:
        deleted = self.memory_manager.delete_memory(memory_id)
        self._record_audit("forget", "deleted" if deleted else "missing", 1 if deleted else 0, (memory_id,))
        return deleted

    def update(self, memory_id: str, **changes: Any) -> Memory | None:
        updated = self.memory_manager.update_memory(memory_id, **changes)
        self._record_audit("update", "updated" if updated is not None else "missing", 1 if updated is not None else 0, (memory_id,))
        return updated

    def archive(self, memory_id: str) -> Memory | None:
        memory = self.get(memory_id)
        if memory is None:
            return None
        return self.update(
            memory_id,
            status=MemoryStatus.ARCHIVED,
            metadata={**dict(memory.metadata), "status": MemoryStatus.ARCHIVED},
        )

    def recent(self, limit: int = 10) -> tuple[Memory, ...]:
        return self.memory_manager.list_memories(limit=limit, offset=0)

    def cleanup(self) -> MemoryConsolidationResult:
        if not self.consolidation_enabled:
            return MemoryConsolidationResult(considered=0, updated=0, archived=0, deleted=0, preview=("consolidation disabled",))
        memories = self.memory_manager.list_memories(limit=self.max_records)
        preview: list[str] = []
        seen: dict[str, str] = {}
        updated = archived = deleted = 0
        considered = len(memories)
        for memory in memories:
            normalized = memory.normalized_content or memory.content.strip().lower()
            if not normalized:
                continue
            if normalized in seen:
                archived_memory = self.memory_manager.update_memory(
                    memory.id,
                    metadata={**dict(memory.metadata), "status": MemoryStatus.SUPERSEDED, "supersedes_memory_id": seen[normalized]},
                )
                if archived_memory is not None:
                    archived += 1
                    updated += 1
                    preview.append(f"superseded {memory.title}")
            else:
                seen[normalized] = memory.id
        self._record_audit("cleanup", "completed", considered, summary=f"updated={updated} archived={archived} deleted={deleted}")
        return MemoryConsolidationResult(considered=considered, updated=updated, archived=archived, deleted=deleted, preview=tuple(preview[:8]))

    def consolidate(self) -> MemoryConsolidationResult:
        return self.cleanup()

    def audit(self, limit: int = 20) -> tuple[MemoryAuditEvent, ...]:
        return tuple(self._audit[-max(1, limit):])

    def status_text(self) -> str:
        status = self.status()
        return (
            f"enabled={'yes' if status.enabled else 'no'} "
            f"local_only={'yes' if status.local_only else 'no'} "
            f"auto_remember={'on' if status.auto_remember else 'off'} "
            f"sessions={status.total_sessions} memories={status.total_memories} "
            f"max_context={status.max_context_items}/{status.max_context_chars}"
        )

    def memory_help(self) -> str:
        return (
            "memory commands: memory status, memory list, memory search <text>, memory show <id>, "
            "memory remember <title> | <content>, memory forget <id>, memory update <id> <content>, "
            "memory archive <id>, memory recent, memory preferences, memory projects, memory audit, "
            "memory cleanup, memory consolidate"
        )

    def handle_command(self, command_name: str, arguments: tuple[str, ...]) -> str:
        name = command_name.strip().lower()
        if name == "memory status":
            return self.status_text()
        if name == "memory help":
            return self.memory_help()
        if name == "memory preferences":
            prefs = self.preferences()
            return (
                "memory preferences: "
                f"local_only={'on' if prefs.local_only else 'off'} "
                f"auto_remember={'on' if prefs.auto_remember else 'off'} "
                f"auto_session_summary={'on' if prefs.auto_session_summary else 'off'} "
                f"sensitive_storage={'on' if prefs.sensitive_storage_enabled else 'off'} "
                f"secret_detection={'on' if prefs.secret_detection_enabled else 'off'}"
            )
        if name == "memory list":
            memories = self.list(limit=min(10, self.max_search_results))
            return self._summarize_memories("Memory list", memories)
        if name == "memory recent":
            memories = self.recent(limit=min(10, self.max_search_results))
            return self._summarize_memories("Recent memories", memories)
        if name == "memory search":
            query = " ".join(arguments).strip()
            results = self.search(query)
            if not results:
                return "No matching memories found."
            return self._summarize_results(results)
        if name == "memory show":
            memory_id = arguments[0] if arguments else ""
            memory = self.get(memory_id)
            if memory is None:
                return "Memory not found."
            return self._format_memory(memory)
        if name == "memory remember":
            title, content = self._split_memory_input(arguments)
            if not content.strip():
                return "Memory content is required."
            created = self.remember(title or self._summarize_title(content), content)
            return f"Memory saved: {created.id}" if created is not None else "Memory not saved."
        if name == "memory forget":
            if not arguments:
                return "Memory id is required."
            return "Memory deleted." if self.forget(arguments[0]) else "Memory not found."
        if name == "memory update":
            if len(arguments) < 2:
                return "Usage: memory update <id> <content>"
            updated = self.update(arguments[0], content=" ".join(arguments[1:]))
            return "Memory updated." if updated is not None else "Memory not found."
        if name == "memory archive":
            if not arguments:
                return "Memory id is required."
            archived = self.archive(arguments[0])
            return "Memory archived." if archived is not None else "Memory not found."
        if name == "memory projects":
            projects = self._list_projects()
            return "Memory projects: " + (", ".join(projects) if projects else "none")
        if name == "memory audit":
            events = self.audit()
            if not events:
                return "No memory audit entries yet."
            return "Memory audit: " + "; ".join(f"{event.action}:{event.status}" for event in events)
        if name == "memory cleanup":
            result = self.cleanup()
            return f"Memory cleanup complete: considered={result.considered} updated={result.updated} archived={result.archived} deleted={result.deleted}"
        if name == "memory consolidate":
            result = self.consolidate()
            return f"Memory consolidation complete: considered={result.considered} updated={result.updated} archived={result.archived} deleted={result.deleted}"
        if name == "memory count":
            return f"Total memories: {self.memory_manager.count_memories()}"
        if name == "memory export":
            return "Memory export is not implemented yet."
        if name == "memory import":
            return "Memory import is not implemented yet."
        return "Unknown memory command."

    def apply_context(self, text: str, *, conversation_id: str, session_id: str | None = None) -> dict[str, Any]:
        summary = self.memory_context(text)
        return {
            "memory_context": {
                "title": summary.title,
                "content": summary.content,
                "memory_ids": summary.memory_ids,
                "memory_type": summary.memory_type,
                "confidence": summary.confidence,
                "tags": summary.tags,
            }
            if summary is not None
            else None,
            "memory_status": self.status_text(),
            "conversation_id": conversation_id,
            "session_id": session_id,
        }

    def note_response(self, user_text: str, assistant_text: str, conversation_id: str, session_id: str | None = None) -> None:
        if self.auto_remember or self.auto_session_summary:
            self.auto_remember_turn(user_text, assistant_text, conversation_id=conversation_id, session_id=session_id)
        self._last_safe_reply = assistant_text

    def repeat_last(self) -> str:
        return self._last_safe_reply or "No remembered reply is available."

    def _summarize_memories(self, heading: str, memories: tuple[Memory, ...]) -> str:
        if not memories:
            return f"{heading}: none"
        return heading + ": " + "; ".join(f"{memory.id} | {memory.title}" for memory in memories[: self.max_context_items])

    def _summarize_results(self, results: tuple[MemorySearchResult, ...]) -> str:
        return "Memory results: " + "; ".join(
            f"{result.memory.id} | {result.memory.title} | {result.relevance:.2f}"
            for result in results[: self.max_context_items]
        )

    def _format_memory(self, memory: Memory) -> str:
        return (
            f"{memory.id} | {memory.title} | {memory.content[:400]} | "
            f"type={memory.memory_type} status={memory.status} tags={', '.join(memory.tags) if memory.tags else 'none'}"
        )

    def _split_memory_input(self, arguments: tuple[str, ...]) -> tuple[str, str]:
        if not arguments:
            return "", ""
        joined = " ".join(arguments)
        if "|" in joined:
            left, right = joined.split("|", 1)
            return left.strip(), right.strip()
        return self._summarize_title(joined), joined.strip()

    def _summarize_title(self, content: str) -> str:
        first_line = content.strip().splitlines()[0] if content.strip() else "Memory"
        return first_line[:64] or "Memory"

    def _build_session_summary(self, user_text: str, assistant_text: str) -> str:
        summary = f"User said: {user_text.strip()}\nAssistant replied: {assistant_text.strip()}"
        return summary[: self.max_context_chars]

    def _tokenize(self, text: str) -> tuple[str, ...]:
        return tuple(token for token in re.split(r"\W+", text.lower()) if token)

    def _score_memory(self, query_tokens: tuple[str, ...], memory: Memory) -> tuple[float, tuple[str, ...]]:
        text = f"{memory.title} {memory.content} {' '.join(memory.tags)}".lower()
        score = 0.0
        reasons: list[str] = []
        for token in query_tokens:
            if token in text:
                score += 1.0
                reasons.append(token)
        if memory.project and memory.project.lower() in text:
            score += 0.2
        if memory.session_id and memory.session_id.lower() in text:
            score += 0.1
        score += min(memory.importance, 5) * 0.05
        score += min(memory.confidence, 1.0) * 0.1
        return score, tuple(reasons)

    def _bounded_snippet(self, content: str, limit: int = 220) -> str:
        text = " ".join(content.strip().split())
        return text[:limit]

    def _list_projects(self) -> tuple[str, ...]:
        memories = self.memory_manager.list_memories(limit=self.max_records)
        projects = sorted({memory.project for memory in memories if memory.project})
        return tuple(projects)

    def _record_audit(self, action: str, status: str, item_count: int, memory_ids: tuple[str, ...] = (), summary: str = "", error: str | None = None) -> None:
        if not self.audit_enabled:
            return
        self._audit.append(
            MemoryAuditEvent(
                timestamp=utc_now(),
                action=action,
                status=status,
                item_count=item_count,
                memory_ids=memory_ids,
                summary=summary[:240],
                error=error,
            )
        )
        if len(self._audit) > self.audit_retention > 0:
            self._audit = self._audit[-self.audit_retention :]
