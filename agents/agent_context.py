"""Runtime context passed to agents."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from agents.agent_checkpoint_store import AgentCheckpointStore
from agents.agent_health import AgentHealth
from agents.agent_metrics import AgentMetrics
from agents.agent_session import AgentSession
from agents.agent_runtime import AgentRuntime
from config.schema import AppSettings


@dataclass(frozen=True, slots=True)
class AgentContext:
    """Reference-only context for running agents."""

    settings: AppSettings | None = None
    memory_manager: Any | None = None
    knowledge_manager: Any | None = None
    task_manager: Any | None = None
    brain_manager: Any | None = None
    plugin_manager: Any | None = None
    provider_router: Any | None = None
    logger: logging.Logger | None = None
    metrics: AgentMetrics | None = None
    health: AgentHealth | None = None
    current_session: AgentSession | None = None
    checkpoint_store: AgentCheckpointStore | None = None
    runtime: AgentRuntime | None = None
