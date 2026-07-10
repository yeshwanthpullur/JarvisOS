"""Agent Creator session models."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from agent_creator.utils import utc_now


@dataclass(frozen=True, slots=True)
class CreatorSession:
    """Session metadata for creation workflows."""

    session_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: str = field(default_factory=lambda: utc_now().isoformat())
    actor: str = "system"

