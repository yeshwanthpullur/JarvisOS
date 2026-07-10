"""Agent objective model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class AgentGoal:
    """Objective passed into orchestration interfaces."""

    description: str
    goal_id: str = field(default_factory=lambda: str(uuid4()))
    priority: int = 100
    metadata: dict[str, Any] = field(default_factory=dict)
