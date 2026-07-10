"""Audit architecture for Agent Creator operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from agent_creator.utils import utc_now


@dataclass(frozen=True, slots=True)
class AuditRecord:
    """Audit record for creator actions."""

    action: str
    actor: str = "system"
    target: str = ""
    outcome: str = "recorded"
    metadata: dict[str, object] = field(default_factory=dict)
    audit_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: utc_now().isoformat())


class AuditManager:
    """Tracks creator audit records."""

    def __init__(self) -> None:
        self._records: list[AuditRecord] = []
        self.initialized = True

    def record(self, action: str, target: str = "", actor: str = "system") -> AuditRecord:
        """Create and store an audit record."""
        record = AuditRecord(action=action, actor=actor, target=target)
        self._records.append(record)
        return record

    def list_records(self) -> tuple[AuditRecord, ...]:
        """List audit records."""
        return tuple(self._records)

