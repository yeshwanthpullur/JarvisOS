"""Agent checkpoint model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class AgentCheckpoint:
    """Serializable agent checkpoint."""

    agent_id: str
    state: str
    payload: dict[str, Any] = field(default_factory=dict)
    checkpoint_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
