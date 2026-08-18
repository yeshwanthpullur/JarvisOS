"""Memory backend adapters that preserve Memory Intelligence authority."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from uuid import uuid4
import re


SECRET = re.compile(r"(?i)(api[_-]?key|password|token|private[_-]?key|secret)\s*[:=]")


class MemoryType(StrEnum):
    SESSION_MEMORY="session_memory"; USER_PREFERENCE_MEMORY="user_preference_memory"; USER_FACT_MEMORY="user_fact_memory"; PROJECT_MEMORY="project_memory"; EPISODIC_MEMORY="episodic_memory"; SEMANTIC_MEMORY="semantic_memory"; KNOWLEDGE_GRAPH_MEMORY="knowledge_graph_memory"; DOCUMENT_MEMORY="document_memory"; RESEARCH_MEMORY="research_memory"; WORKFLOW_MEMORY="workflow_memory"; TASK_MEMORY="task_memory"; GOAL_MEMORY="goal_memory"; SYSTEM_OPERATIONAL_MEMORY="system_operational_memory"


@dataclass(frozen=True, slots=True)
class RetrievalEvidence:
    memory_id: str; namespace: str; memory_type: MemoryType; content: str; provenance: str; confidence: str; score: float; source_timestamp: str; verified: bool; superseded: bool = False


@dataclass(slots=True)
class MemoryBackendState:
    backend_id: str; role: str; detected: bool = False; enabled: bool = False; healthy: bool = False; reason: str = "Not configured."


class MemoryRetrievalControlPlane:
    def __init__(self, *, max_results: int = 8, max_context_chars: int = 3000) -> None:
        self.max_results = min(max(1, max_results), 20); self.max_context_chars = min(max(200, max_context_chars), 12000)
        self.backends = {
            "mem0": MemoryBackendState("mem0", "memory_framework"), "qdrant": MemoryBackendState("qdrant", "primary_vector"), "chromadb": MemoryBackendState("chromadb", "backup_vector"), "faiss": MemoryBackendState("faiss", "temporary_vector"), "graphiti": MemoryBackendState("graphiti", "temporal_graph"), "local_embedding": MemoryBackendState("local_embedding", "embedding_provider"),
        }
        self._evidence: dict[str, RetrievalEvidence] = {}; self.audit: list[dict[str, object]] = []

    def propose(self, namespace: str, content: str, memory_type: MemoryType, provenance: str, *, authoritative: bool = False, verified: bool = False) -> RetrievalEvidence:
        if not authoritative:
            raise PermissionError("memory_intelligence_authority_required")
        if SECRET.search(content):
            raise ValueError("sensitive_credential_memory_rejected")
        item = RetrievalEvidence(f"mem-{uuid4().hex[:12]}", namespace[:80], memory_type, content[:2000], provenance[:120], "confirmed" if verified else "unverified", 1.0, datetime.now(timezone.utc).isoformat(), verified)
        self._evidence[item.memory_id] = item; self.audit.append({"operation": "authoritative_write", "memory_id": item.memory_id, "namespace": item.namespace, "source": item.provenance, "result": "stored", "backend": "authoritative_metadata"}); self.audit = self.audit[-100:]
        return item

    def search(self, query: str, namespace: str) -> tuple[RetrievalEvidence, ...]:
        words = set(re.findall(r"[a-z0-9]+", query.lower()))
        ranked = []
        for item in self._evidence.values():
            if item.namespace != namespace or item.superseded:
                continue
            terms = set(re.findall(r"[a-z0-9]+", item.content.lower())); score = len(words & terms) / max(1, len(words))
            if score:
                ranked.append((score, item))
        selected = []
        budget = 0
        for score, item in sorted(ranked, key=lambda pair: (pair[0], pair[1].verified), reverse=True)[: self.max_results]:
            if budget + len(item.content) > self.max_context_chars:
                continue
            budget += len(item.content); selected.append(RetrievalEvidence(item.memory_id, item.namespace, item.memory_type, item.content, item.provenance, item.confidence, score, item.source_timestamp, item.verified, item.superseded))
        return tuple(selected)

    def forget(self, memory_id: str, *, authoritative: bool = False) -> bool:
        if not authoritative:
            raise PermissionError("memory_intelligence_authority_required")
        removed = self._evidence.pop(memory_id, None); self.audit.append({"operation": "forget", "memory_id": memory_id, "result": "removed" if removed else "not_found", "backend": "authoritative_metadata"}); return removed is not None

    def status(self) -> dict[str, object]:
        return {"authority": "memory_intelligence", "automatic_write": False, "records": len(self._evidence), "active_namespaces": len({item.namespace for item in self._evidence.values()}), "semantic_backend": "metadata_only", "graph": "degraded", "embedding": "unconfigured", "fallback": "bounded_lexical", "context_budget_chars": self.max_context_chars}
