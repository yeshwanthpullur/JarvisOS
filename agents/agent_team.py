"""Agent team models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import uuid4

from agents.agent_capabilities import AgentCapability
from agents.agent_health import AgentHealth
from agents.agent_metrics import AgentMetrics
from agents.agent_permissions import AgentPermission
from agents.agent_status import AgentStatus


class AgentTeamType(StrEnum):
    """Supported future team types."""

    SINGLE = "single"
    PAIR = "pair"
    STATIC = "static"
    DYNAMIC = "dynamic"
    PIPELINE = "pipeline"
    SUPERVISOR = "supervisor"
    HIERARCHICAL = "hierarchical"
    SWARM = "swarm"
    COORDINATOR = "coordinator"
    DISTRIBUTED = "distributed"


@dataclass(slots=True)
class AgentTeam:
    """Team metadata for future multi-agent collaboration."""

    members: tuple[str, ...]
    leader: str | None = None
    team_type: AgentTeamType = AgentTeamType.STATIC
    capabilities: tuple[AgentCapability, ...] = ()
    permissions: tuple[AgentPermission, ...] = ()
    status: AgentStatus = AgentStatus.IDLE
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    health: AgentHealth = field(default_factory=AgentHealth)
    configuration: dict[str, Any] = field(default_factory=dict)
    shared_memory_interface: Any | None = None
    team_id: str = field(default_factory=lambda: str(uuid4()))
